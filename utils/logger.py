"""
Logging configuration for the PSS RAG system.
Provides centralized logging with proper formatting and log levels.
"""

import logging
import os
from datetime import datetime
from typing import Optional
from config import Config

class RAGLogger:
    """Centralized logger for the PSS RAG system"""
    
    def __init__(self, name: str = "PSS_RAG"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with file and console handlers"""
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
            
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(Config.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(Config.LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, extra: Optional[dict] = None):
        """Log info message"""
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, exc_info: bool = True, extra: Optional[dict] = None):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, extra=extra)
    
    def warning(self, message: str, extra: Optional[dict] = None):
        """Log warning message"""
        self.logger.warning(message, extra=extra)
    
    def debug(self, message: str, extra: Optional[dict] = None):
        """Log debug message"""
        self.logger.debug(message, extra=extra)
    
    def log_api_call(self, endpoint: str, user_query: str, response_time: float, success: bool):
        """Log API call details for monitoring"""
        log_data = {
            'endpoint': endpoint,
            'query_length': len(user_query),
            'response_time': response_time,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            self.info(f"API call successful - {endpoint} - {response_time:.2f}s", extra=log_data)
        else:
            self.error(f"API call failed - {endpoint} - {response_time:.2f}s", extra=log_data)
    
    def log_security_event(self, event_type: str, details: str, severity: str = "INFO"):
        """Log security-related events"""
        log_data = {
            'event_type': event_type,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        
        message = f"Security Event: {event_type} - {details}"
        
        if severity == "CRITICAL":
            self.error(message, extra=log_data)
        elif severity == "WARNING":
            self.warning(message, extra=log_data)
        else:
            self.info(message, extra=log_data)

# Global logger instance
logger = RAGLogger() 