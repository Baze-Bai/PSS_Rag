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
        
        print("🔍 Validating configuration...")
        
        # Check required AWS credentials
        if not cls.AWS_ACCESS_KEY_ID or cls.AWS_ACCESS_KEY_ID == "your_aws_access_key_here":
            missing.append("AWS_ACCESS_KEY_ID")
            print("❌ AWS_ACCESS_KEY_ID is missing or using placeholder value")
        else:
            print(f"✅ AWS_ACCESS_KEY_ID: {cls.AWS_ACCESS_KEY_ID[:4]}...{cls.AWS_ACCESS_KEY_ID[-4:]}")
            
        if not cls.AWS_SECRET_ACCESS_KEY or cls.AWS_SECRET_ACCESS_KEY == "your_aws_secret_key_here":
            missing.append("AWS_SECRET_ACCESS_KEY")
            print("❌ AWS_SECRET_ACCESS_KEY is missing or using placeholder value")
        else:
            print(f"✅ AWS_SECRET_ACCESS_KEY: ***...{cls.AWS_SECRET_ACCESS_KEY[-4:]}")
        
        # Check file paths
        if not os.path.exists(cls.DATA_FILE):
            warnings.append(f"Data file not found: {cls.DATA_FILE}")
            print(f"⚠️ Data file not found: {cls.DATA_FILE}")
        else:
            print(f"✅ Data file found: {cls.DATA_FILE}")
        
        # Provide helpful messages
        if missing:
            print("\n🛠️ To fix configuration issues:")
            print("1. Make sure you have a .env file in your project root")
            print("2. Add your actual AWS credentials to the .env file:")
            print("   AWS_ACCESS_KEY_ID=AKIA...")
            print("   AWS_SECRET_ACCESS_KEY=...")
            print("3. Remove any quotes around the values")
            print("4. Ensure no spaces around the = sign")
            
        print(f"\n📊 Configuration status: {'✅ Valid' if len(missing) == 0 else '❌ Invalid'}")
            
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
    
    @classmethod
    def print_current_config(cls):
        """Print current configuration for debugging"""
        print("\n📋 Current Configuration:")
        print(f"   AWS Region: {cls.AWS_REGION}")
        print(f"   AWS Model: {cls.AWS_MODEL_ID}")
        print(f"   Embedding Model: {cls.EMBEDDING_MODEL}")
        print(f"   Max Tokens: {cls.MAX_TOKENS}")
        print(f"   Temperature: {cls.LLM_TEMPERATURE}")
        print(f"   Top K Results: {cls.TOP_K_RESULTS}")
        print(f"   Data File: {cls.DATA_FILE}")
        print(f"   Log Level: {cls.LOG_LEVEL}")

if __name__ == "__main__":
    # Test configuration
    Config.print_current_config()
    validation = Config.validate_config()
    print(f"\nValidation result: {validation}") 