"""
Configuration management for the PSS RAG system.
Centralizes all configuration settings for better maintainability.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the PSS RAG system"""
    
    # === AWS BEDROCK CONFIGURATION ===
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_MODEL_ID = os.getenv("AWS_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # === RAG CONFIGURATION ===
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "my_faiss.index")
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
    
    # === LLM PARAMETERS ===
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.05"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))
    
    # === DATA PATHS ===
    DATA_FILE = os.getenv("DATA_FILE", "Baze_project/Projects that Have been worked on in the last 8 years and the active employees.csv")
    RESUMES_FOLDER = os.getenv("RESUMES_FOLDER", "Baze_project/Resumes")
    PROJECTS_FOLDER = os.getenv("PROJECTS_FOLDER", "Baze_project/_Marketing Project Sheets")
    
    # === MONGODB CONFIGURATION (if needed) ===
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "pss_rag")
    
    # === SECURITY CONFIGURATION ===
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "1000"))
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
    
    # === LOGGING CONFIGURATION ===
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return any missing required settings"""
        missing = []
        warnings = []
        
        # Check required AWS credentials
        if not cls.AWS_ACCESS_KEY_ID:
            missing.append("AWS_ACCESS_KEY_ID")
        if not cls.AWS_SECRET_ACCESS_KEY:
            missing.append("AWS_SECRET_ACCESS_KEY")
            
        # Check file paths
        if not os.path.exists(cls.DATA_FILE):
            warnings.append(f"Data file not found: {cls.DATA_FILE}")
            
        return {
            "missing_required": missing,
            "warnings": warnings,
            "is_valid": len(missing) == 0
        }
    
    @classmethod
    def get_aws_config(cls) -> Dict[str, str]:
        """Get AWS configuration dictionary"""
        return {
            "region_name": cls.AWS_REGION,
            "aws_access_key_id": cls.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": cls.AWS_SECRET_ACCESS_KEY
        } 