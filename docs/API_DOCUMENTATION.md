# PSS RAG System - API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core APIs](#core-apis)
4. [Configuration APIs](#configuration-apis)
5. [Monitoring APIs](#monitoring-apis)
6. [Security APIs](#security-apis)
7. [Error Responses](#error-responses)
8. [Rate Limiting](#rate-limiting)
9. [Examples](#examples)

## Overview

The PSS RAG System provides both internal APIs for component interaction and external interfaces through the Streamlit web application. This documentation covers the internal API structure and external integration points.

### Base Information
- **Version**: 1.0.0
- **Protocol**: HTTP/HTTPS
- **Data Format**: JSON
- **Authentication**: AWS Credentials + Session Management

## Authentication

### AWS Bedrock Authentication
```python
# Environment Variables Required
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

### Session Management
- **Client Identification**: Automatic session-based tracking
- **Rate Limiting**: Per-client rate limiting
- **Session Timeout**: Configurable (default: 3600 seconds)

## Core APIs

### 1. LLM Service API

#### Generate Response
**Method**: `llm_service.generate_response(prompt, context=None)`

**Parameters**:
```python
{
    "prompt": "string",        # Required: User question/prompt
    "context": "string"        # Optional: Context for RAG
}
```

**Response**:
```python
{
    "success": boolean,
    "response": "string",      # Generated response text
    "response_time": float,    # Response time in seconds
    "model_id": "string",      # AWS Bedrock model identifier
    "token_count": integer,    # Number of tokens in response
    "error": "string"          # Error message if success=false
}
```

**Example**:
```python
from services.llm_service import llm_service

response = llm_service.generate_response(
    prompt="What projects are available?",
    context="Project documents context..."
)

if response["success"]:
    print(f"Response: {response['response']}")
    print(f"Time: {response['response_time']:.2f}s")
else:
    print(f"Error: {response['error']}")
```

#### Health Check
**Method**: `llm_service.health_check()`

**Response**:
```python
{
    "healthy": boolean,
    "response_time": float,
    "model_id": "string",
    "timestamp": float,
    "error": "string"          # Present if healthy=false
}
```

#### Performance Statistics
**Method**: `llm_service.get_performance_stats()`

**Response**:
```python
{
    "total_requests": integer,
    "average_response_time": float,
    "error_rate": float,       # Percentage
    "success_rate": float      # Percentage
}
```

### 2. Security API

#### Input Validation
**Method**: `security_manager.validate_input(user_input)`

**Parameters**:
```python
{
    "user_input": "string"     # Input to validate
}
```

**Response**:
```python
{
    "is_valid": boolean,
    "cleaned_input": "string", # Sanitized input or error message
}
```

#### Rate Limit Check
**Method**: `security_manager.check_rate_limit(client_id)`

**Parameters**:
```python
{
    "client_id": "string"      # Client identifier
}
```

**Response**:
```python
{
    "allowed": boolean,
    "remaining_requests": integer
}
```

#### Content Policy Check
**Method**: `security_manager.check_content_policy(text)`

**Parameters**:
```python
{
    "text": "string"           # Content to check
}
```

**Response**:
```python
{
    "is_valid": boolean,
    "message": "string"        # Policy result message
}
```

#### Sensitive Data Redaction
**Method**: `security_manager.redact_sensitive_data(text)`

**Parameters**:
```python
{
    "text": "string"           # Text to redact
}
```

**Response**:
```python
{
    "redacted_text": "string" # Text with sensitive data replaced
}
```

### 3. Document Processing API

#### Store Data
**Method**: `store_data()`

**Response**:
```python
{
    "chunks": ["string"],      # List of document chunks
    "index": faiss.Index,      # FAISS search index
    "file_names": ["string"]   # List of source file names
}
```

#### Process Query
**Method**: `rag_system.process_query(question)`

**Parameters**:
```python
{
    "question": "string"       # User question
}
```

**Response**:
```python
{
    "top_chunks": ["string"],     # Relevant document chunks
    "top_files": ["string"],      # Source file names
    "project_numbers": ["string"] # Extracted project numbers
}
```

## Configuration APIs

### Configuration Validation
**Method**: `Config.validate_config()`

**Response**:
```python
{
    "missing_required": ["string"],  # List of missing required configs
    "warnings": ["string"],          # List of warning messages
    "is_valid": boolean              # Overall validation status
}
```

### AWS Configuration
**Method**: `Config.get_aws_config()`

**Response**:
```python
{
    "region_name": "string",
    "aws_access_key_id": "string",
    "aws_secret_access_key": "string"
}
```

### Configuration Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `AWS_REGION` | string | "us-east-1" | AWS region for Bedrock |
| `AWS_MODEL_ID` | string | "anthropic.claude-3-sonnet-20240229-v1:0" | Bedrock model ID |
| `EMBEDDING_MODEL` | string | "sentence-transformers/all-MiniLM-L6-v2" | Embedding model |
| `TOP_K_RESULTS` | integer | 5 | Number of search results |
| `LLM_TEMPERATURE` | float | 0.05 | LLM temperature setting |
| `MAX_TOKENS` | integer | 1024 | Maximum response tokens |
| `MAX_QUERY_LENGTH` | integer | 1000 | Maximum query length |
| `RATE_LIMIT_PER_MINUTE` | integer | 30 | Rate limit per client |
| `SESSION_TIMEOUT` | integer | 3600 | Session timeout in seconds |
| `LOG_LEVEL` | string | "INFO" | Logging level |

## Monitoring APIs

### Logger API

#### Log API Call
**Method**: `logger.log_api_call(endpoint, user_query, response_time, success)`

**Parameters**:
```python
{
    "endpoint": "string",      # API endpoint name
    "user_query": "string",    # User query (will be hashed)
    "response_time": float,    # Response time in seconds
    "success": boolean         # Whether call succeeded
}
```

#### Log Security Event
**Method**: `logger.log_security_event(event_type, details, severity)`

**Parameters**:
```python
{
    "event_type": "string",    # Type of security event
    "details": "string",       # Event details
    "severity": "string"       # "INFO", "WARNING", or "CRITICAL"
}
```

### Session Information
**Method**: `security_manager.get_session_info()`

**Response**:
```python
{
    "client_id": "string",
    "rate_limit_remaining": integer,
    "session_start": datetime,
    "requests_made": integer
}
```

## Security APIs

### Security Events

#### Rate Limit Exceeded
```python
{
    "event": "RATE_LIMIT_EXCEEDED",
    "client_id": "string",
    "timestamp": "ISO8601",
    "severity": "WARNING"
}
```

#### Malicious Input Detected
```python
{
    "event": "MALICIOUS_INPUT_DETECTED",
    "pattern": "string",
    "timestamp": "ISO8601",
    "severity": "CRITICAL"
}
```

#### Content Policy Violation
```python
{
    "event": "CONTENT_POLICY_VIOLATION",
    "category": "string",
    "timestamp": "ISO8601",
    "severity": "WARNING"
}
```

## Error Responses

### Common Error Codes

#### Configuration Errors
```python
{
    "error_code": "CONFIG_ERROR",
    "message": "Missing required configuration: AWS_ACCESS_KEY_ID",
    "details": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
}
```

#### Authentication Errors
```python
{
    "error_code": "AUTH_ERROR",
    "message": "AWS credentials invalid or expired",
    "timestamp": "ISO8601"
}
```

#### Rate Limit Errors
```python
{
    "error_code": "RATE_LIMIT_ERROR",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60,
    "remaining": 0
}
```

#### Validation Errors
```python
{
    "error_code": "VALIDATION_ERROR",
    "message": "Input contains potentially malicious content",
    "field": "user_input"
}
```

#### Service Errors
```python
{
    "error_code": "SERVICE_ERROR",
    "message": "AWS Bedrock service temporarily unavailable",
    "retry_after": 300,
    "internal_error": "ThrottlingException"
}
```

## Rate Limiting

### Rate Limit Headers
When rate limiting is active, responses include:
```python
{
    "X-RateLimit-Limit": 30,      # Requests per minute
    "X-RateLimit-Remaining": 25,  # Remaining requests
    "X-RateLimit-Reset": 1642680000 # Reset timestamp
}
```

### Rate Limit Configuration
```python
# In .env file
RATE_LIMIT_PER_MINUTE=30        # Requests per minute
RATE_LIMIT_WINDOW=60            # Window in seconds
```

## Examples

### Complete Query Flow
```python
from Rag import RAGSystem

# Initialize system
rag_system = RAGSystem()

# Process a query
question = "What projects involve machine learning?"

# Step 1: Security validation
is_valid, cleaned_question = security_manager.validate_input(question)
if not is_valid:
    print(f"Validation failed: {cleaned_question}")
    exit()

# Step 2: Process query
top_chunks, top_files, project_numbers = rag_system.process_query(cleaned_question)

# Step 3: Generate responses
for chunk, filename in zip(top_chunks, top_files):
    response = llm_service.generate_response(cleaned_question, chunk)
    
    if response["success"]:
        print(f"File: {filename}")
        print(f"Response: {response['response']}")
        print(f"Time: {response['response_time']:.2f}s")
    else:
        print(f"Error processing {filename}: {response['error']}")
```

### Health Check Example
```python
# Check system health
health = llm_service.health_check()
config_valid = Config.validate_config()

if health["healthy"] and config_valid["is_valid"]:
    print("✅ System is healthy")
else:
    print("❌ System has issues:")
    if not health["healthy"]:
        print(f"LLM Service: {health.get('error', 'Unknown error')}")
    if not config_valid["is_valid"]:
        print(f"Config: {config_valid['missing_required']}")
```

### Security Event Monitoring
```python
# Monitor security events
session_info = security_manager.get_session_info()
print(f"Client: {session_info['client_id']}")
print(f"Remaining requests: {session_info['rate_limit_remaining']}")
print(f"Requests made: {session_info['requests_made']}")

# Check for suspicious activity
if session_info['requests_made'] > 20:
    logger.log_security_event(
        "HIGH_USAGE_DETECTED",
        f"Client made {session_info['requests_made']} requests",
        "WARNING"
    )
```

### Performance Monitoring
```python
# Get performance statistics
stats = llm_service.get_performance_stats()
print(f"Total Requests: {stats['total_requests']}")
print(f"Success Rate: {stats['success_rate']:.1f}%")
print(f"Average Response Time: {stats['average_response_time']:.2f}s")

# Alert on performance issues
if stats['success_rate'] < 95.0:
    logger.log_security_event(
        "LOW_SUCCESS_RATE",
        f"Success rate dropped to {stats['success_rate']:.1f}%",
        "WARNING"
    )
```

## Integration Guide

### Streamlit Integration
The system integrates with Streamlit for the web interface:

```python
import streamlit as st
from Rag import RAGSystem

# Initialize in Streamlit
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = RAGSystem()

# Use cached system
rag_system = st.session_state.rag_system
```

### External Integration
For external systems integrating with the PSS RAG System:

```python
# Example external integration
import requests
import json

class PSS_RAG_Client:
    def __init__(self, base_url, aws_credentials):
        self.base_url = base_url
        self.credentials = aws_credentials
    
    def query(self, question):
        # Your integration logic here
        pass
``` 