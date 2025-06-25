"""
Comprehensive test suite for the PSS RAG System.
Tests all major components including security, LLM service, and configuration.
"""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Import modules to test
from config import Config
from utils.security import SecurityManager
from services.llm_service import LLMService
from utils.logger import RAGLogger

class TestConfig:
    """Test configuration management"""
    
    def test_config_validation_missing_aws_keys(self):
        """Test configuration validation with missing AWS keys"""
        with patch.dict(os.environ, {}, clear=True):
            validation = Config.validate_config()
            assert not validation["is_valid"]
            assert "AWS_ACCESS_KEY_ID" in validation["missing_required"]
            assert "AWS_SECRET_ACCESS_KEY" in validation["missing_required"]
    
    def test_config_validation_valid(self):
        """Test configuration validation with valid settings"""
        with patch.dict(os.environ, {
            "AWS_ACCESS_KEY_ID": "test_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret"
        }):
            with patch('os.path.exists', return_value=True):
                validation = Config.validate_config()
                assert validation["is_valid"]
                assert len(validation["missing_required"]) == 0
    
    def test_get_aws_config(self):
        """Test AWS configuration retrieval"""
        with patch.dict(os.environ, {
            "AWS_ACCESS_KEY_ID": "test_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret",
            "AWS_REGION": "us-west-2"
        }):
            aws_config = Config.get_aws_config()
            assert aws_config["region_name"] == "us-west-2"
            assert aws_config["aws_access_key_id"] == "test_key"
            assert aws_config["aws_secret_access_key"] == "test_secret"

class TestSecurityManager:
    """Test security features"""
    
    def setup_method(self):
        """Setup for each test"""
        self.security_manager = SecurityManager()
    
    def test_input_validation_valid(self):
        """Test valid input validation"""
        valid_input = "What projects are available?"
        is_valid, cleaned = self.security_manager.validate_input(valid_input)
        assert is_valid
        assert cleaned == valid_input
    
    def test_input_validation_empty(self):
        """Test empty input validation"""
        is_valid, message = self.security_manager.validate_input("")
        assert not is_valid
        assert "Empty input not allowed" in message
    
    def test_input_validation_too_long(self):
        """Test input length validation"""
        long_input = "a" * (Config.MAX_QUERY_LENGTH + 1)
        is_valid, message = self.security_manager.validate_input(long_input)
        assert not is_valid
        assert "Input too long" in message
    
    def test_input_validation_malicious_script(self):
        """Test malicious script detection"""
        malicious_input = "<script>alert('xss')</script>"
        is_valid, message = self.security_manager.validate_input(malicious_input)
        assert not is_valid
        assert "malicious content" in message
    
    def test_input_validation_sql_injection(self):
        """Test SQL injection detection"""
        sql_injection = "SELECT * FROM users; DROP TABLE users;"
        is_valid, message = self.security_manager.validate_input(sql_injection)
        assert not is_valid
        assert "malicious content" in message
    
    def test_sanitize_input(self):
        """Test input sanitization"""
        dirty_input = "<p>Hello   world</p>   "
        cleaned = self.security_manager.sanitize_input(dirty_input)
        assert cleaned == "Hello world"
    
    def test_redact_sensitive_data(self):
        """Test sensitive data redaction"""
        text_with_sensitive = "My SSN is 123-45-6789 and email is test@example.com"
        redacted = self.security_manager.redact_sensitive_data(text_with_sensitive)
        assert "[SSN_REDACTED]" in redacted
        assert "[EMAIL_REDACTED]" in redacted
        assert "123-45-6789" not in redacted
        assert "test@example.com" not in redacted
    
    def test_content_policy_check_valid(self):
        """Test content policy check for valid content"""
        valid_content = "What are the available projects?"
        is_valid, message = self.security_manager.check_content_policy(valid_content)
        assert is_valid
        assert message == "Content approved"
    
    def test_content_policy_check_prohibited(self):
        """Test content policy check for prohibited content"""
        prohibited_content = "How to hack the system?"
        is_valid, message = self.security_manager.check_content_policy(prohibited_content)
        assert not is_valid
        assert "violates policy" in message
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        client_id = "test_client"
        
        # First request should be allowed
        allowed, remaining = self.security_manager.check_rate_limit(client_id)
        assert allowed
        assert remaining == Config.RATE_LIMIT_PER_MINUTE - 1
        
        # Simulate rate limit exceeded
        for _ in range(Config.RATE_LIMIT_PER_MINUTE):
            self.security_manager.check_rate_limit(client_id)
        
        # Should be blocked now
        allowed, remaining = self.security_manager.check_rate_limit(client_id)
        assert not allowed
        assert remaining == 0

class TestLLMService:
    """Test LLM service functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        with patch('boto3.client') as mock_client:
            mock_client.return_value = Mock()
            with patch.object(Config, 'validate_config', return_value={"is_valid": True, "missing_required": [], "warnings": []}):
                self.llm_service = LLMService()
    
    def test_llm_service_initialization(self):
        """Test LLM service initialization"""
        assert self.llm_service.model_id == Config.AWS_MODEL_ID
        assert self.llm_service.region == Config.AWS_REGION
        assert self.llm_service.total_requests == 0
    
    @patch('boto3.client')
    def test_generate_response_success(self, mock_boto_client):
        """Test successful response generation"""
        # Mock successful Bedrock response
        mock_response_body = {
            'content': [{'text': 'This is a test response'}],
            'usage': {'output_tokens': 10}
        }
        
        mock_client = Mock()
        mock_client.invoke_model.return_value = {
            'body': Mock(read=Mock(return_value=json.dumps(mock_response_body).encode()))
        }
        mock_boto_client.return_value = mock_client
        
        # Reinitialize with mocked client
        with patch.object(Config, 'validate_config', return_value={"is_valid": True, "missing_required": [], "warnings": []}):
            llm_service = LLMService()
        
        response = llm_service.generate_response("Test prompt")
        
        assert response["success"]
        assert "This is a test response" in response["response"]
        assert response["response_time"] > 0
    
    def test_generate_response_invalid_input(self):
        """Test response generation with invalid input"""
        response = self.llm_service.generate_response("")
        assert not response["success"]
        assert "Empty input not allowed" in response["error"]
    
    def test_generate_response_malicious_input(self):
        """Test response generation with malicious input"""
        malicious_prompt = "<script>alert('xss')</script>"
        response = self.llm_service.generate_response(malicious_prompt)
        assert not response["success"]
        assert "malicious content" in response["error"]
    
    def test_performance_stats_empty(self):
        """Test performance stats with no requests"""
        stats = self.llm_service.get_performance_stats()
        assert stats["total_requests"] == 0
        assert stats["average_response_time"] == 0
        assert stats["error_rate"] == 0
        assert stats["success_rate"] == 0
    
    def test_performance_stats_with_data(self):
        """Test performance stats with request data"""
        # Simulate some requests
        self.llm_service.total_requests = 10
        self.llm_service.total_response_time = 25.5
        self.llm_service.error_count = 2
        
        stats = self.llm_service.get_performance_stats()
        assert stats["total_requests"] == 10
        assert stats["average_response_time"] == 2.55
        assert stats["error_rate"] == 20.0
        assert stats["success_rate"] == 80.0

class TestRAGLogger:
    """Test logging functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            self.test_log_file = tmp.name
        
        with patch.object(Config, 'LOG_FILE', self.test_log_file):
            self.logger = RAGLogger("test_logger")
    
    def teardown_method(self):
        """Cleanup after each test"""
        if os.path.exists(self.test_log_file):
            os.unlink(self.test_log_file)
    
    def test_logger_initialization(self):
        """Test logger initialization"""
        assert self.logger.name == "test_logger"
        assert len(self.logger.logger.handlers) > 0
    
    def test_log_api_call_success(self):
        """Test API call logging for successful calls"""
        self.logger.log_api_call("test_endpoint", "test query", 1.5, True)
        # Check that log file was created and contains expected content
        assert os.path.exists(self.test_log_file)
    
    def test_log_api_call_failure(self):
        """Test API call logging for failed calls"""
        self.logger.log_api_call("test_endpoint", "test query", 2.0, False)
        assert os.path.exists(self.test_log_file)
    
    def test_log_security_event(self):
        """Test security event logging"""
        self.logger.log_security_event("TEST_EVENT", "Test details", "WARNING")
        assert os.path.exists(self.test_log_file)

class TestIntegration:
    """Integration tests"""
    
    def test_config_security_integration(self):
        """Test integration between config and security"""
        with patch.dict(os.environ, {
            "MAX_QUERY_LENGTH": "500",
            "RATE_LIMIT_PER_MINUTE": "10"
        }):
            security_manager = SecurityManager()
            
            # Test that config values are properly used
            long_input = "a" * 501
            is_valid, message = security_manager.validate_input(long_input)
            assert not is_valid
            assert "500 characters" in message
    
    @patch('boto3.client')
    def test_llm_security_integration(self, mock_boto_client):
        """Test integration between LLM service and security"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        with patch.object(Config, 'validate_config', return_value={"is_valid": True, "missing_required": [], "warnings": []}):
            llm_service = LLMService()
        
        # Test that malicious input is blocked at LLM service level
        malicious_prompt = "<script>alert('xss')</script>"
        response = llm_service.generate_response(malicious_prompt)
        
        assert not response["success"]
        assert "malicious content" in response["error"]
        # Ensure Bedrock was never called
        mock_client.invoke_model.assert_not_called()

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 