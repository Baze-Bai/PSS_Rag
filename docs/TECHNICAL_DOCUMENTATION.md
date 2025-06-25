# PSS RAG System - Technical Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Security Implementation](#security-implementation)
6. [Performance Considerations](#performance-considerations)
7. [Error Handling](#error-handling)
8. [Monitoring and Logging](#monitoring-and-logging)

## System Overview

The PSS (Professional Services System) RAG (Retrieval-Augmented Generation) System is an AI-powered document retrieval and question-answering platform designed for professional services organizations. The system combines semantic search capabilities with large language models to provide intelligent responses based on project documents, employee resumes, and organizational data.

### Key Features
- **Semantic Document Search**: Uses FAISS (Facebook AI Similarity Search) for efficient vector-based document retrieval
- **AWS Bedrock Integration**: Leverages Claude-3-Sonnet for natural language generation
- **Security-First Design**: Comprehensive input validation, rate limiting, and privacy controls
- **Real-time Monitoring**: Performance tracking and health checks
- **Scalable Architecture**: Modular design for easy maintenance and expansion

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │  Security Layer │    │   Config Mgmt   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────────────────────┼─────────────────────────────────┐
│                            RAG System                              │
├─────────────────┬─────────────────┬─────────────────┬─────────────┤
│  LLM Service    │  Vector Search  │  Data Manager   │   Logger    │
│  (AWS Bedrock)  │    (FAISS)      │   (Store_data)  │             │
└─────────────────┴─────────────────┴─────────────────┴─────────────┘
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AWS Bedrock   │    │  FAISS Index    │    │  Document Store │
│   Claude-3      │    │   Embeddings    │    │   PDF Files     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Architecture
```
config.py                 # Centralized configuration management
├── utils/
│   ├── logger.py         # Logging and monitoring
│   └── security.py       # Security controls and validation
├── services/
│   └── llm_service.py    # AWS Bedrock integration
├── Rag.py                # Main application logic
├── Store_data.py         # Document processing and indexing
└── tests/                # Comprehensive test suite
```

## Component Details

### 1. Configuration Management (`config.py`)
- **Purpose**: Centralized configuration for all system components
- **Features**:
  - Environment variable management
  - AWS credential handling
  - Validation of required settings
  - Default value management
- **Key Methods**:
  - `validate_config()`: Validates configuration completeness
  - `get_aws_config()`: Returns AWS client configuration

### 2. Security Manager (`utils/security.py`)
- **Purpose**: Comprehensive security controls
- **Features**:
  - Input validation and sanitization
  - Rate limiting (30 requests/minute default)
  - Malicious content detection
  - Sensitive data redaction
  - Content policy enforcement
- **Security Patterns Detected**:
  - XSS attempts (`<script>` tags)
  - SQL injection patterns
  - Code injection attempts
  - Data URI attacks

### 3. LLM Service (`services/llm_service.py`)
- **Purpose**: AWS Bedrock integration with robust error handling
- **Features**:
  - Retry logic with exponential backoff
  - Response validation
  - Performance monitoring
  - Health checks
- **Error Handling**:
  - Rate limiting detection
  - Service quota management
  - Network error recovery
  - Graceful degradation

### 4. Logger (`utils/logger.py`)
- **Purpose**: Comprehensive logging and monitoring
- **Features**:
  - Structured logging with multiple handlers
  - Security event tracking
  - API call monitoring
  - Performance metrics
- **Log Levels**:
  - DEBUG: Detailed diagnostic information
  - INFO: General operational messages
  - WARNING: Potential issues
  - ERROR: Error conditions

### 5. RAG System (`Rag.py`)
- **Purpose**: Main application orchestration
- **Features**:
  - Streamlit UI management
  - Query processing pipeline
  - Document retrieval coordination
  - Response generation
- **Caching Strategy**:
  - `@st.cache_data`: Data loading functions
  - `@st.cache_resource`: Model and index loading

## Data Flow

### Query Processing Pipeline
1. **Input Validation**
   - Security checks (malicious content, length limits)
   - Rate limiting verification
   - Content policy validation

2. **Document Retrieval**
   - Query embedding generation using Sentence Transformers
   - FAISS similarity search (top-k results)
   - Project number extraction from filenames

3. **Response Generation**
   - Context preparation for each relevant document
   - AWS Bedrock API calls with retry logic
   - Response validation and sanitization

4. **Result Presentation**
   - Formatted response display
   - Related project information
   - Document download links
   - Performance metrics

### Data Processing Flow
```
User Query → Security Validation → Embedding → FAISS Search → 
Document Chunks → LLM Processing → Response Validation → 
UI Display → Logging
```

## Security Implementation

### Input Security
- **Length Validation**: Maximum 1000 characters (configurable)
- **Pattern Matching**: Regular expressions to detect malicious content
- **Sanitization**: HTML tag removal and whitespace normalization
- **Content Policy**: Prohibition of harmful content categories

### API Security
- **Rate Limiting**: 30 requests per minute per client (configurable)
- **Authentication**: AWS credentials validation
- **Input/Output Validation**: Both request and response validation
- **Sensitive Data Redaction**: Automatic removal of PII

### Infrastructure Security
- **Environment Variables**: Secure credential storage
- **Logging**: Security event tracking
- **Error Handling**: No sensitive data in error messages
- **Session Management**: Client identification and tracking

## Performance Considerations

### Optimization Strategies
1. **Caching**
   - Streamlit native caching for models and data
   - FAISS index persistence
   - Configuration caching

2. **Batch Processing**
   - Multiple document processing in parallel
   - Efficient vector operations with NumPy

3. **Resource Management**
   - Memory-efficient embedding model loading
   - Connection pooling for AWS services
   - Proper resource cleanup

### Performance Metrics
- **Response Time**: Average response time tracking
- **Success Rate**: Request success percentage
- **Error Rate**: Failed request percentage
- **Throughput**: Requests per minute

### Scalability Features
- **Stateless Design**: No server-side session state
- **Modular Architecture**: Independent component scaling
- **Configuration-Driven**: Environment-specific settings
- **Health Checks**: Service availability monitoring

## Error Handling

### Error Categories
1. **Configuration Errors**
   - Missing AWS credentials
   - Invalid file paths
   - Malformed configuration

2. **Runtime Errors**
   - AWS service unavailability
   - Network connectivity issues
   - Resource exhaustion

3. **User Input Errors**
   - Invalid queries
   - Rate limit exceeded
   - Policy violations

### Error Recovery Strategies
- **Retry Logic**: Exponential backoff for transient failures
- **Graceful Degradation**: Partial functionality during service issues
- **User Feedback**: Clear error messages without exposing internals
- **Logging**: Comprehensive error tracking for debugging

## Monitoring and Logging

### Monitoring Components
1. **Health Checks**
   - LLM service availability
   - Response time monitoring
   - Error rate tracking

2. **Performance Metrics**
   - Request volume
   - Success/failure rates
   - Average response times

3. **Security Monitoring**
   - Failed authentication attempts
   - Rate limit violations
   - Malicious input detection

### Log Structure
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "component": "llm_service",
  "event": "api_call_success",
  "details": {
    "response_time": 1.23,
    "query_length": 45,
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0"
  }
}
```

### Alerting
- **Critical Errors**: Immediate notification
- **Performance Degradation**: Threshold-based alerts
- **Security Events**: Real-time security monitoring
- **Resource Usage**: Capacity planning alerts

## Technology Stack

### Core Technologies
- **Python 3.8+**: Primary programming language
- **Streamlit**: Web application framework
- **AWS Bedrock**: Large language model service
- **FAISS**: Vector similarity search
- **Sentence Transformers**: Text embedding generation

### Supporting Libraries
- **NumPy**: Numerical computing
- **Pandas**: Data manipulation
- **Boto3**: AWS SDK
- **Tenacity**: Retry logic
- **pytest**: Testing framework

### Infrastructure
- **AWS**: Cloud infrastructure
- **Environment Variables**: Configuration management
- **File System**: Document storage
- **Logging**: File-based logging with rotation

## Deployment Considerations

### Environment Requirements
- Python 3.8+ runtime
- AWS credentials configuration
- Sufficient memory for embedding models
- Network access to AWS Bedrock

### Configuration Management
- Environment-specific `.env` files
- Configurable rate limits and timeouts
- Logging level configuration
- AWS region and model selection

### Monitoring Setup
- Log aggregation configuration
- Health check endpoints
- Performance metric collection
- Error alerting configuration 