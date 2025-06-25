"""
LLM Service for AWS Bedrock integration.
Simplified and optimized version with fallback to mock service.
"""

import json
import time
import boto3
import streamlit as st
from typing import Dict, Optional
from botocore.exceptions import ClientError, BotoCoreError, NoCredentialsError, EndpointConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

from utils.logger import logger
from utils.security import security_manager

# Load environment variables from .env file
load_dotenv()

# === CONFIGURATION ===
REGION = "us-east-1"
MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

class LLMService:
    """Service class for AWS Bedrock LLM interactions with mock fallback"""
    
    def __init__(self):
        self.model_id = MODEL_ID
        self.region = REGION
        self.client = None
        self.use_mock = False  # Flag to use mock service
        self.mock_service = None
        
        # Performance tracking
        self.total_requests = 0
        self.total_response_time = 0.0
        self.error_count = 0
        
        # Initialize client
        self._initialize_client()
    
    def _initialize_mock_service(self):
        """Initialize mock service as fallback"""
        try:
            from services.mock_llm_service import mock_llm_service
            self.mock_service = mock_llm_service
            self.use_mock = True
            logger.info("Initialized mock LLM service as fallback")
        except ImportError:
            logger.error("Failed to import mock service")
    
    @st.cache_resource
    def _get_bedrock_client(_self):
        """Create and cache the AWS Bedrock runtime client."""
        try:
            return boto3.client("bedrock-runtime", region_name=REGION)
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise ValueError("❌ AWS credentials not found. Please set them in your .env file or use `aws configure`.")
        except EndpointConnectionError:
            logger.error("Could not connect to Bedrock endpoint")
            raise ValueError("❌ Could not connect to Bedrock endpoint. Check your AWS region and network.")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {str(e)}")
            raise ValueError(f"❌ Failed to initialize Bedrock client: {str(e)}")
    
    def _initialize_client(self):
        """Initialize AWS Bedrock client"""
        try:
            self.client = self._get_bedrock_client()
            logger.info("AWS Bedrock client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS Bedrock client: {str(e)}")
            logger.info("Falling back to mock service...")
            self._initialize_mock_service()
    
    def generate_response(self, prompt: str, context: Optional[str] = None) -> Dict[str, any]:
        """Generate response with automatic fallback to mock service"""
        
        # If we're already using mock service, delegate directly
        if self.use_mock and self.mock_service:
            return self._generate_mock_response(prompt, context)
        
        start_time = time.time()
        self.total_requests += 1
        
        try:
            # Input validation
            if not prompt or not prompt.strip():
                return {
                    "success": False,
                    "error": "⚠️ Input cannot be empty.",
                    "response": None,
                    "response_time": 0
                }
            
            # Security validation
            is_valid, cleaned_prompt = security_manager.validate_input(prompt)
            if not is_valid:
                return {
                    "success": False,
                    "error": cleaned_prompt,
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
            
            # Get client (may need to reinitialize if failed before)
            if not self.client:
                self.client = self._get_bedrock_client()
            
            # Prepare conversation for the new API format
            messages = [
                {
                    "role": "user",
                    "content": [{"text": full_prompt}]
                }
            ]
            
            logger.debug(f"Sending request to Bedrock - Model: {self.model_id}")
            
            # Call Bedrock using the converse API (newer format)
            response = self.client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={
                    "maxTokens": 1024,
                    "temperature": 0.05,
                    "topP": 0.9
                }
            )
            
            # Validate and extract response
            try:
                reply = response["output"]["message"]["content"][0]["text"]
            except (KeyError, IndexError, TypeError) as e:
                logger.error("Unexpected response format from Bedrock")
                logger.error(f"Full response: {response}")
                return {
                    "success": False,
                    "error": "❌ Unexpected response format from Bedrock.",
                    "response": None,
                    "response_time": time.time() - start_time
                }
            
            # Redact sensitive information from response
            safe_response = security_manager.redact_sensitive_data(reply)
            
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            # Log successful interaction
            security_manager.log_user_interaction(cleaned_prompt, safe_response)
            logger.log_api_call("bedrock_converse", cleaned_prompt, response_time, True)
            
            return {
                "success": True,
                "response": safe_response,
                "response_time": response_time,
                "model_id": self.model_id,
                "token_count": response.get('usage', {}).get('outputTokens', 0)
            }
                
        except ClientError as e:
            # Check if it's a permissions error
            if "AccessDeniedException" in str(e):
                logger.warning("AWS Bedrock access denied. Switching to mock service...")
                self._initialize_mock_service()
                if self.mock_service:
                    return self._generate_mock_response(prompt, context)
            
            self.error_count += 1
            response_time = time.time() - start_time
            error_msg = f"❌ [Bedrock API Error] {str(e)}"
            
            logger.error(f"Bedrock API error: {str(e)}")
            logger.log_api_call("bedrock_converse", prompt, response_time, False)
            
            return {
                "success": False,
                "error": error_msg,
                "response": None,
                "response_time": response_time
            }
            
        except Exception as e:
            # For any other error, try falling back to mock
            logger.warning(f"Bedrock error, trying mock service: {str(e)}")
            self._initialize_mock_service()
            if self.mock_service:
                return self._generate_mock_response(prompt, context)
            
            self.error_count += 1
            response_time = time.time() - start_time
            error_msg = f"❌ [Unexpected Error] {str(e)}"
            
            logger.error(f"Unexpected error generating response: {str(e)}")
            logger.log_api_call("bedrock_converse", prompt, response_time, False)
            
            return {
                "success": False,
                "error": error_msg,
                "response": None,
                "response_time": response_time
            }
    
    def _generate_mock_response(self, prompt: str, context: Optional[str] = None) -> Dict[str, any]:
        """Generate response using mock service with context awareness"""
        try:
            # Use mock service
            if self.mock_service:
                mock_result = self.mock_service.generate_response(prompt, context)
                
                # Add note about using mock service
                if mock_result["success"]:
                    mock_result["response"] += "\n\n⚠️ **Using Mock Service**: AWS Bedrock permissions are required for full AI capabilities. Please request access to bedrock:InvokeModel permission."
                    mock_result["service_type"] = "mock"
                
                return mock_result
            else:
                return {
                    "success": False,
                    "error": "Both Bedrock and mock services unavailable",
                    "response": None,
                    "response_time": 0
                }
        except Exception as e:
            logger.error(f"Mock service error: {str(e)}")
            return {
                "success": False,
                "error": f"Mock service error: {str(e)}",
                "response": None,
                "response_time": 0
            }
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Get performance statistics"""
        base_stats = {
            "total_requests": self.total_requests,
            "average_response_time": 0,
            "error_rate": 0,
            "success_rate": 0,
            "service_type": "mock" if self.use_mock else "bedrock"
        }
        
        if self.total_requests == 0:
            return base_stats
        
        success_rate = ((self.total_requests - self.error_count) / self.total_requests) * 100
        avg_response_time = self.total_response_time / self.total_requests
        error_rate = (self.error_count / self.total_requests) * 100
        
        base_stats.update({
            "average_response_time": round(avg_response_time, 2),
            "error_rate": round(error_rate, 2),
            "success_rate": round(success_rate, 2)
        })
        
        # Add mock service stats if using mock
        if self.use_mock and self.mock_service:
            mock_stats = self.mock_service.get_performance_stats()
            base_stats["mock_requests"] = mock_stats["total_requests"]
        
        return base_stats
    
    def health_check(self) -> Dict[str, any]:
        """Perform health check"""
        try:
            # If using mock service, use its health check
            if self.use_mock and self.mock_service:
                health = self.mock_service.health_check()
                health["service_type"] = "mock"
                health["message"] = "Using mock service due to AWS Bedrock permissions"
                return health
            
            # Try Bedrock health check
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
                "region": self.region,
                "timestamp": time.time(),
                "service_type": "mock" if self.use_mock else "bedrock",
                "error": test_response.get("error") if not test_response["success"] else None
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": time.time(),
                "service_type": "unknown"
            }

# Global LLM service instance
llm_service = LLMService() 