#!/usr/bin/env python3
"""
Configuration Diagnosis Script for PSS RAG System
Helps identify and resolve environment variable configuration issues
"""

import os
import sys
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def check_python_dotenv():
    """Check if python-dotenv is installed"""
    try:
        import dotenv
        print("✅ python-dotenv is installed")
        return True
    except ImportError:
        print("❌ python-dotenv is NOT installed")
        print("   Install with: pip install python-dotenv")
        return False

def check_env_file():
    """Check for .env file existence and content"""
    env_paths = [
        ".env",
        "../.env",
        "../../.env"
    ]
    
    print("\n🔍 Checking for .env file...")
    
    for path in env_paths:
        if os.path.exists(path):
            print(f"✅ Found .env file at: {os.path.abspath(path)}")
            
            # Read and display (safely)
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()
                    print(f"   File contains {len(lines)} lines")
                    
                    # Check for AWS keys (without showing values)
                    has_access_key = any('AWS_ACCESS_KEY_ID' in line for line in lines)
                    has_secret_key = any('AWS_SECRET_ACCESS_KEY' in line for line in lines)
                    
                    print(f"   AWS_ACCESS_KEY_ID present: {'✅' if has_access_key else '❌'}")
                    print(f"   AWS_SECRET_ACCESS_KEY present: {'✅' if has_secret_key else '❌'}")
                    
                    # Show structure (without values)
                    print("\n   .env file structure:")
                    for i, line in enumerate(lines[:10], 1):  # Show first 10 lines only
                        if line.strip() and not line.startswith('#'):
                            key = line.split('=')[0] if '=' in line else line.strip()
                            print(f"   {i:2d}: {key}=***")
                        elif line.strip():
                            print(f"   {i:2d}: {line.strip()}")
                    
                    if len(lines) > 10:
                        print(f"   ... and {len(lines) - 10} more lines")
                        
            except Exception as e:
                print(f"   ❌ Error reading .env file: {e}")
            
            return path
    
    print("❌ No .env file found in expected locations")
    return None

def check_environment_variables():
    """Check current environment variables"""
    print("\n🔍 Checking environment variables...")
    
    aws_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION',
        'AWS_MODEL_ID'
    ]
    
    for var in aws_vars:
        value = os.getenv(var)
        if value:
            # Show first and last 4 chars for security
            if len(value) > 8:
                display_value = f"{value[:4]}...{value[-4:]}"
            else:
                display_value = "***"
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")

def test_dotenv_loading():
    """Test loading .env file manually"""
    print("\n🔍 Testing .env file loading...")
    
    try:
        from dotenv import load_dotenv
        
        # Try loading from current directory
        result = load_dotenv()
        print(f"   load_dotenv() result: {result}")
        
        # Try loading with explicit path
        env_file = ".env"
        if os.path.exists(env_file):
            result = load_dotenv(env_file)
            print(f"   load_dotenv('{env_file}') result: {result}")
            
            # Check if variables are now available
            test_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
            for var in test_vars:
                value = os.getenv(var)
                print(f"   After loading - {var}: {'✅ Set' if value else '❌ Not set'}")
        
    except Exception as e:
        print(f"   ❌ Error testing dotenv loading: {e}")

def create_env_template():
    """Create a template .env file"""
    template_content = """# PSS RAG System Environment Configuration
# Copy this file to .env and fill in your actual values

# === AWS BEDROCK CONFIGURATION ===
# Your AWS credentials for Bedrock access
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
AWS_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# === RAG CONFIGURATION ===
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
FAISS_INDEX_PATH=my_faiss.index
TOP_K_RESULTS=5

# === LLM PARAMETERS ===
LLM_TEMPERATURE=0.05
MAX_TOKENS=1024

# === DATA PATHS ===
DATA_FILE=Baze_project/Projects that Have been worked on in the last 8 years and the active employees.csv
RESUMES_FOLDER=Baze_project/Resumes
PROJECTS_FOLDER=Baze_project/_Marketing Project Sheets

# === SECURITY CONFIGURATION ===
SESSION_TIMEOUT=3600
MAX_QUERY_LENGTH=1000
RATE_LIMIT_PER_MINUTE=30

# === LOGGING CONFIGURATION ===
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
"""
    
    try:
        with open('.env.template', 'w') as f:
            f.write(template_content)
        print("✅ Created .env.template file")
        print("   Copy this to .env and fill in your AWS credentials")
    except Exception as e:
        print(f"❌ Error creating template: {e}")

def test_config_import():
    """Test importing and using the config module"""
    print("\n🔍 Testing config module import...")
    
    try:
        from config import Config
        print("✅ Config module imported successfully")
        
        # Test validation
        validation = Config.validate_config()
        print(f"   Configuration validation: {validation}")
        
        if not validation['is_valid']:
            print("   ❌ Configuration is invalid")
            print(f"   Missing: {validation['missing_required']}")
            if validation['warnings']:
                print(f"   Warnings: {validation['warnings']}")
        else:
            print("   ✅ Configuration is valid")
            
    except Exception as e:
        print(f"   ❌ Error importing config: {e}")

def provide_solutions():
    """Provide step-by-step solutions"""
    print_header("SOLUTIONS")
    
    print("🔧 Solution 1: Create/Fix .env file")
    print("   1. Create a .env file in your project root directory")
    print("   2. Add your AWS credentials (no quotes, no spaces around =):")
    print("      AWS_ACCESS_KEY_ID=AKIA...")
    print("      AWS_SECRET_ACCESS_KEY=...")
    print("      AWS_REGION=us-east-1")
    
    print("\n🔧 Solution 2: Check file format")
    print("   Ensure your .env file has:")
    print("   - No spaces around the = sign")
    print("   - No quotes around values")
    print("   - One variable per line")
    print("   - Unix line endings (LF, not CRLF)")
    
    print("\n🔧 Solution 3: Set environment variables directly")
    print("   Windows:")
    print("      set AWS_ACCESS_KEY_ID=your_key")
    print("      set AWS_SECRET_ACCESS_KEY=your_secret")
    print("   Linux/Mac:")
    print("      export AWS_ACCESS_KEY_ID=your_key")
    print("      export AWS_SECRET_ACCESS_KEY=your_secret")
    
    print("\n🔧 Solution 4: Install/reinstall python-dotenv")
    print("   pip install --upgrade python-dotenv")
    
    print("\n🔧 Solution 5: Check file location")
    print("   Make sure .env is in the same directory as your Python scripts")
    print("   Current working directory:", os.getcwd())

def main():
    """Main diagnostic function"""
    print_header("PSS RAG SYSTEM - CONFIGURATION DIAGNOSIS")
    
    # Check dependencies
    dotenv_ok = check_python_dotenv()
    
    # Check .env file
    env_file = check_env_file()
    
    # Check environment variables
    check_environment_variables()
    
    # Test dotenv loading
    if dotenv_ok:
        test_dotenv_loading()
    
    # Test config import
    test_config_import()
    
    # Create template if needed
    if not env_file:
        print("\n🔧 Creating .env template...")
        create_env_template()
    
    # Provide solutions
    provide_solutions()
    
    print_header("DIAGNOSIS COMPLETE")
    print("If you're still having issues:")
    print("1. Check the solutions above")
    print("2. Ensure your .env file is properly formatted")
    print("3. Verify your AWS credentials are correct")
    print("4. Try restarting your Python session")

if __name__ == "__main__":
    main() 