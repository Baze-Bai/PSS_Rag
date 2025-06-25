"""
LLM Service for AWS Bedrock integration.
Provides robust error handling, retry logic, and performance monitoring.
"""

import json
import time
import boto3
from typing import Dict, Optional, List
from botocore.exceptions import ClientError, BotoCoreError
from tenacity import retry, stop_after_attempt, wait_exponential

from config import Config
from utils.logger import logger
from utils.security import security_manager

class LLMService:
    """Service class for AWS Bedrock LLM interactions"""
    
    def __init__(self):
        self.client = None
        self.model_id = Config.AWS_MODEL_ID
        self.region = Config.AWS_REGION
        self._initialize_client()
        
        # Performance tracking
        self.total_requests = 0
        self.total_response_time = 0.0
        self.error_count = 0
    
    def _initialize_client(self):
        """Initialize AWS Bedrock client with proper error handling"""
        try:
            aws_config = Config.get_aws_config()
            
            # Validate configuration
            config_validation = Config.validate_config()
            if not config_validation["is_valid"]:
                missing = config_validation["missing_required"]
                raise ValueError(f"Missing required configuration: {', '.join(missing)}")
            
            self.client = boto3.client('bedrock-runtime', **aws_config)
            logger.info("AWS Bedrock client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS Bedrock client: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _call_bedrock_with_retry(self, body: Dict) -> Dict:
        """Call Bedrock with retry logic"""
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            return json.loads(response['body'].read())
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS Bedrock ClientError: {error_code} - {str(e)}")
            
            # Handle specific error cases
            if error_code in ['ThrottlingException', 'ServiceQuotaExceededException']:
                logger.warning("Rate limiting detected, backing off...")
                raise  # Will trigger retry
            elif error_code == 'ValidationException':
                logger.error("Invalid request parameters")
                raise ValueError("Invalid request parameters") from e
            else:
                raise
                
        except BotoCoreError as e:
            logger.error(f"AWS BotoCoreError: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Bedrock: {str(e)}")
            raise
    
    def generate_response(self, prompt: str, context: Optional[str] = None) -> Dict[str, any]:
        """
        Generate response from Bedrock model with comprehensive error handling.
        
        Args:
            prompt: User prompt/question
            context: Optional context for RAG
            
        Returns:
            Dict containing response, metadata, and performance info
        """
        start_time = time.time()
        self.total_requests += 1
        
        try:
            # Security validation
            is_valid, cleaned_prompt = security_manager.validate_input(prompt)
            if not is_valid:
                return {
                    "success": False,
                    "error": cleaned_prompt,  # Error message
                    "response": None,
                    "response_time": 0
                }
            
            # Content policy check
            policy_ok, policy_msg = security_manager.check_content_policy(cleaned_prompt)
            if not policy_ok:
                return {
                    "success": False,
                    "error": policy_msg,
                    "response": None,
                    "response_time": 0
                }
            
            # Prepare full prompt with context
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {cleaned_prompt}\n\nPlease provide a helpful and accurate answer based on the context provided."
            else:
                full_prompt = cleaned_prompt
            
            # Prepare request body
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": Config.MAX_TOKENS,
                "messages": [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                "temperature": Config.LLM_TEMPERATURE
            }
            
            logger.debug(f"Sending request to Bedrock - Model: {self.model_id}")
            
            # Call Bedrock with retry logic
            response_body = self._call_bedrock_with_retry(body)
            
            # Extract response text
            if 'content' in response_body and len(response_body['content']) > 0:
                response_text = response_body['content'][0]['text']
                
                # Redact sensitive information from response
                safe_response = security_manager.redact_sensitive_data(response_text)
                
                response_time = time.time() - start_time
                self.total_response_time += response_time
                
                # Log successful interaction
                security_manager.log_user_interaction(cleaned_prompt, safe_response)
                logger.log_api_call("bedrock_generate", cleaned_prompt, response_time, True)
                
                return {
                    "success": True,
                    "response": safe_response,
                    "response_time": response_time,
                    "model_id": self.model_id,
                    "token_count": response_body.get('usage', {}).get('output_tokens', 0)
                }
            else:
                logger.error("Invalid response format from Bedrock")
                return {
                    "success": False,
                    "error": "Invalid response format from Bedrock",
                    "response": None,
                    "response_time": time.time() - start_time
                }
                
        except Exception as e:
            self.error_count += 1
            response_time = time.time() - start_time
            
            logger.error(f"Error generating response: {str(e)}")
            logger.log_api_call("bedrock_generate", prompt, response_time, False)
            
            return {
                "success": False,
                "error": f"Service temporarily unavailable: {str(e)}",
                "response": None,
                "response_time": response_time
            }
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Get performance statistics"""
        if self.total_requests == 0:
            return {
                "total_requests": 0,
                "average_response_time": 0,
                "error_rate": 0,
                "success_rate": 0
            }
        
        success_rate = ((self.total_requests - self.error_count) / self.total_requests) * 100
        avg_response_time = self.total_response_time / self.total_requests
        error_rate = (self.error_count / self.total_requests) * 100
        
        return {
            "total_requests": self.total_requests,
            "average_response_time": round(avg_response_time, 2),
            "error_rate": round(error_rate, 2),
            "success_rate": round(success_rate, 2)
        }
    
    def health_check(self) -> Dict[str, any]:
        """Perform health check on the LLM service"""
        try:
            test_response = self.generate_response("Hello, please respond with 'Service is healthy'")
            
            is_healthy = (
                test_response["success"] and 
                test_response["response"] and
                "healthy" in test_response["response"].lower()
            )
            
            return {
                "healthy": is_healthy,
                "response_time": test_response["response_time"],
                "model_id": self.model_id,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": time.time()
            }

# Global LLM service instance
llm_service = LLMService() 