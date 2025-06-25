"""
Mock LLM Service for testing when AWS Bedrock is not available.
"""

import time
import random
from typing import Dict, Optional

class MockLLMService:
    """Mock LLM service that provides realistic responses"""
    
    def __init__(self):
        self.model_id = "mock-claude-3-sonnet"
        self.region = "us-east-1"
        self.total_requests = 0
        self.total_response_time = 0.0
        self.error_count = 0
    
    def generate_response(self, prompt: str, context: Optional[str] = None) -> Dict[str, any]:
        """Generate a mock response"""
        start_time = time.time()
        self.total_requests += 1
        
        # Simulate processing time
        time.sleep(random.uniform(0.5, 1.5))
        
        mock_response = f"Mock response to: {prompt[:50]}... This is a demonstration response."
        
        response_time = time.time() - start_time
        self.total_response_time += response_time
        
        return {
            "success": True,
            "response": mock_response,
            "response_time": response_time,
            "model_id": self.model_id,
            "token_count": len(mock_response.split())
        }
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Get performance statistics"""
        if self.total_requests == 0:
            return {"total_requests": 0, "average_response_time": 0, "error_rate": 0, "success_rate": 100}
        
        avg_response_time = self.total_response_time / self.total_requests
        return {
            "total_requests": self.total_requests,
            "average_response_time": round(avg_response_time, 2),
            "error_rate": 0,
            "success_rate": 100
        }
    
    def health_check(self) -> Dict[str, any]:
        """Perform health check"""
        return {
            "healthy": True,
            "response_time": 0.5,
            "model_id": self.model_id,
            "region": self.region,
            "timestamp": time.time(),
            "service_type": "mock"
        }

mock_llm_service = MockLLMService() 