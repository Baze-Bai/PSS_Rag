# PSS RAG System - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [AWS Setup](#aws-setup)
6. [Local Deployment](#local-deployment)
7. [Production Deployment](#production-deployment)
8. [Docker Deployment](#docker-deployment)
9. [Monitoring Setup](#monitoring-setup)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **Memory**: Minimum 8GB RAM (16GB+ recommended)
- **Storage**: At least 5GB free space
- **Network**: Internet connection for AWS Bedrock access

### Required Accounts
- **AWS Account**: With Bedrock access enabled
- **Git**: For source code management

## Environment Setup

### 1. Python Environment
```bash
# Check Python version
python --version  # Should be 3.8+

# Create virtual environment
python -m venv pss_rag_env

# Activate virtual environment
# On Windows:
pss_rag_env\Scripts\activate
# On macOS/Linux:
source pss_rag_env/bin/activate
```

### 2. Clone Repository
```bash
git clone https://github.com/your-org/pss-rag-system.git
cd pss-rag-system
```

## Installation

### 1. Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(streamlit|boto3|faiss|sentence-transformers)"
```

### 2. Download Models
```bash
# Download embedding model (automatic on first run)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### 3. Prepare Data
```bash
# Ensure data directories exist
mkdir -p Baze_project/Resumes
mkdir -p Baze_project/_Marketing\ Project\ Sheets/
mkdir -p logs

# Process documents (if not already done)
python Store_data.py
```

## Configuration

### 1. Environment Variables
Create a `.env` file in the project root:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
AWS_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# RAG Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
FAISS_INDEX_PATH=my_faiss.index
TOP_K_RESULTS=5

# LLM Parameters
LLM_TEMPERATURE=0.05
MAX_TOKENS=1024

# Data Paths
DATA_FILE=Baze_project/Projects that Have been worked on in the last 8 years and the active employees.csv
RESUMES_FOLDER=Baze_project/Resumes
PROJECTS_FOLDER=Baze_project/_Marketing Project Sheets

# Security Configuration
MAX_QUERY_LENGTH=1000
RATE_LIMIT_PER_MINUTE=30
SESSION_TIMEOUT=3600

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 2. Configuration Validation
```bash
# Test configuration
python -c "from config import Config; print(Config.validate_config())"
```

## AWS Setup

### 1. Enable AWS Bedrock
1. **Login to AWS Console**
2. **Navigate to AWS Bedrock**
3. **Enable Model Access**:
   - Go to "Model access" in the left sidebar
   - Request access to "Claude 3 Sonnet"
   - Wait for approval (usually instant for most accounts)

### 2. Create IAM User
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
            ]
        }
    ]
}
```

### 3. Test AWS Connection
```bash
# Test AWS credentials
python -c "
from services.llm_service import llm_service
health = llm_service.health_check()
print('AWS Connection:', 'OK' if health['healthy'] else 'FAILED')
"
```

## Local Deployment

### 1. Development Mode
```bash
# Activate virtual environment
source pss_rag_env/bin/activate  # or pss_rag_env\Scripts\activate on Windows

# Run Streamlit application
streamlit run Rag.py --server.port 8501

# Access application
# Open http://localhost:8501 in your browser
```

### 2. Development with Debug
```bash
# Set debug logging
export LOG_LEVEL=DEBUG  # or set LOG_LEVEL=DEBUG on Windows

# Run with debug output
streamlit run Rag.py --server.port 8501 --logger.level debug
```

### 3. Testing
```bash
# Run test suite
pytest tests/ -v

# Run specific test categories
pytest tests/test_rag_system.py::TestSecurity -v
pytest tests/test_rag_system.py::TestLLMService -v
```

## Production Deployment

### 1. Environment Setup
```bash
# Production environment variables
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export RATE_LIMIT_PER_MINUTE=60
export SESSION_TIMEOUT=1800
```

### 2. Streamlit Configuration
Create `.streamlit/config.toml`:
```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 10

[logger]
level = "info"

[client]
showErrorDetails = false
toolbarMode = "minimal"

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

### 3. Process Management
```bash
# Using PM2 (recommended)
npm install -g pm2

# Create PM2 configuration
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'pss-rag-system',
    script: 'streamlit',
    args: 'run Rag.py --server.port 8501 --server.address 0.0.0.0',
    interpreter: 'python',
    cwd: '/path/to/pss-rag-system',
    env: {
      'PYTHONPATH': '/path/to/pss-rag-system'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '2G'
  }]
}
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 4. Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}
```

## Docker Deployment

### 1. Dockerfile
```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "Rag.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Docker Compose
```yaml
version: '3.8'

services:
  pss-rag:
    build: .
    ports:
      - "8501:8501"
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION=${AWS_REGION}
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./Baze_project:/app/Baze_project
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - pss-rag
    restart: unless-stopped
```

### 3. Build and Deploy
```bash
# Build Docker image
docker build -t pss-rag-system .

# Run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f pss-rag

# Scale if needed
docker-compose up -d --scale pss-rag=3
```

## Monitoring Setup

### 1. Application Monitoring
```bash
# Install monitoring dependencies
pip install prometheus-client grafana-api

# Create monitoring endpoint
# Add to Rag.py:
from prometheus_client import Counter, Histogram, generate_latest
import time

REQUEST_COUNT = Counter('pss_rag_requests_total', 'Total requests')
REQUEST_DURATION = Histogram('pss_rag_request_duration_seconds', 'Request duration')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

### 2. Log Monitoring
```bash
# Using ELK Stack or similar
# Configure log shipping
tail -f logs/app.log | logstash -f logstash.conf

# Or use journald for systemd systems
sudo journalctl -u pss-rag-system -f
```

### 3. Health Monitoring
```bash
# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/_stcore/health)
if [ $response -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $response)"
    exit 1
fi
EOF

chmod +x health_check.sh

# Add to crontab for monitoring
echo "*/5 * * * * /path/to/health_check.sh" | crontab -
```

## Troubleshooting

### Common Issues

#### 1. AWS Connection Issues
```bash
# Check AWS credentials
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Verify model access
aws bedrock get-foundation-model --model-identifier anthropic.claude-3-sonnet-20240229-v1:0 --region us-east-1
```

#### 2. Memory Issues
```bash
# Monitor memory usage
ps aux | grep streamlit
free -h

# Increase swap if needed (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3. Port Issues
```bash
# Check if port is in use
netstat -tlnp | grep 8501
lsof -i :8501

# Kill process using port
sudo kill -9 $(lsof -t -i:8501)
```

#### 4. Permission Issues
```bash
# Fix file permissions
chmod -R 755 /path/to/pss-rag-system
chown -R $USER:$USER /path/to/pss-rag-system

# Create log directory
mkdir -p logs
chmod 755 logs
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
streamlit run Rag.py --logger.level debug --server.runOnSave false
```

### Log Analysis
```bash
# Check application logs
tail -f logs/app.log

# Check for errors
grep "ERROR" logs/app.log

# Check for security events
grep "Security Event" logs/app.log

# Monitor performance
grep "response_time" logs/app.log | tail -10
```

## Security Considerations

### 1. Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw deny 8501/tcp  # Block direct Streamlit access
sudo ufw enable
```

### 2. SSL/TLS Setup
```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. Environment Security
```bash
# Secure .env file
chmod 600 .env
chown root:root .env

# Use secrets management in production
# AWS Secrets Manager, HashiCorp Vault, etc.
```

## Backup and Recovery

### 1. Data Backup
```bash
# Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz \
    .env \
    Baze_project/ \
    my_faiss.index \
    logs/

# Automated backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/pss-rag"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/pss-rag-$DATE.tar.gz \
    .env Baze_project/ my_faiss.index logs/
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF
```

### 2. Recovery Procedure
```bash
# Stop application
pm2 stop pss-rag-system

# Restore from backup
tar -xzf backup-20240115.tar.gz

# Restart application
pm2 start pss-rag-system
```

## Scaling Considerations

### 1. Horizontal Scaling
- Load balancer configuration
- Session affinity considerations
- Shared storage for FAISS index

### 2. Performance Optimization
- FAISS index optimization
- Model caching strategies
- Request batching

### 3. Resource Planning
- CPU: 2-4 cores per instance
- Memory: 8-16GB per instance
- Storage: 10GB+ for documents and indexes
- Network: 1Gbps+ for AWS connectivity 