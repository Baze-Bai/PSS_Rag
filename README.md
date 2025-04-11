# PSS RAG System

## Overview
This project implements a Retrieval-Augmented Generation (RAG) system for P&S Engineering, enabling users to query project information through a natural language interface. The system integrates PDF data extraction, vector search, and LLM-based question answering to provide relevant information about engineering projects.

## Features
- Extract and index text from project PDFs
- Search for relevant project information using natural language queries
- View related employee data and work hours for projects
- Access and download relevant employee resumes and project documentation
- AI-powered responses with multiple LLM options (Llama3, deepseek-r1)

## System Components

### Data Processing
- `Extract_PDF.py`: Extracts text content from PDF files
- `Store_data.py`: Embeds text chunks using sentence transformers and builds a FAISS index
- `Store_chunks.py`: Stores extracted text chunks in MongoDB

### Search and Retrieval
- `Find_project.py`: Identifies relevant employees and projects based on project numbers
- `Rag.py`: Main application implementing the RAG system with Streamlit UI

## Detailed File Descriptions

### `Extract_PDF.py`
This file handles the extraction of text from PDF documents in the project sheets directory. It includes:
- `extract_chunks_from_pdf(directory)`: The main function that processes PDF files from a specified directory
- Text cleaning to remove unnecessary content (e.g., "www.psands.com")
- Tokenization and chunk filtering to improve result quality
- Text preprocessing to handle short lines and maintain document context
- Returns both the extracted text chunks and corresponding file names (project identifiers)

### `Store_data.py`
Responsible for creating and managing vector embeddings for the text data:
- Loads the extracted text chunks from PDF files
- Uses the SentenceTransformer model ('sentence-transformers/all-MiniLM-L6-v2') to convert text to vector embeddings
- Creates a FAISS index using Inner Product similarity for efficient semantic search
- Normalizes embeddings for cosine similarity comparisons
- Persists the index to disk as "my_faiss.index"
- Returns the original chunks, the index object, and file names for later retrieval

### `Store_chunks.py`
Handles the storage of text chunks in MongoDB for persistence:
- Calls `store_data()` to get chunks and the index
- Connects to a local MongoDB instance
- Creates or clears the "pdf_chunks" collection in the "ps_rag" database
- Stores each text chunk with a unique identifier
- Provides output confirmation of successful storage

### `Find_project.py`
Facilitates connecting project information with employee data:
- Defines paths for accessing resumes and project sheets
- `get_filtered_data_by_projects(proj_numbers, df)`: Filters employee records by project numbers
- `find_resumes(employees)`: Locates resume files for relevant employees
- Links employee data with relevant projects and documents

### `Rag.py`
The main application file implementing the RAG system and Streamlit UI:
- Creates an interactive web interface with Streamlit
- Implements the query processing pipeline:
  - Accepts natural language queries from users
  - Encodes queries into vector embeddings
  - Searches the FAISS index for semantically similar text chunks
  - Retrieves project information, employee data, and related documents
  - Calls LLM models (Llama3 or deepseek-r1) to generate answers
  - Displays results with quality assessments
- Implements caching for improved performance
- Provides document download functionality
- Handles the integration of all system components

### `.env.example`
Template for environment configuration:
- API keys for external services
- Database connection settings
- Application configuration for Ollama

### `requirements.txt`
Lists all Python dependencies required to run the system:
- ML and vector search libraries (FAISS, sentence-transformers)
- PDF processing libraries (PyMuPDF, pytesseract)
- Database connectivity (pymongo)
- Web UI framework (streamlit)
- LLM integration (ollama, transformers)

## Setup and Installation

### Prerequisites
- Python 3.8+
- Required libraries: streamlit, pandas, faiss, sentence-transformers, pymongo, PyMuPDF, pytesseract, ollama

### Installation Steps
1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up local Ollama instance for LLM support
4. Create a `.env` file with required API keys (DEEP_SEEK_API_KEY)

### Project Structure
```
.
├── _Marketing Project Sheets/  # Project PDF documents
├── Baze_project/               # Main data directory
│   ├── Resumes/                # Employee resume files
│   ├── _Marketing Project Sheets/ # Project documentation
│   └── Projects that Have been worked on in the last 8 years and the active employees.csv
├── Extract_PDF.py              # PDF text extraction
├── Find_project.py             # Project and employee lookup
├── Rag.py                      # Main application
├── Store_data.py               # Vector embedding and indexing
└── Store_chunks.py             # Database storage
```

## Usage
1. Run the application:
   ```
   streamlit run Rag.py
   ```
2. Enter your question in the search box
3. View AI-generated answers along with relevant project information
4. Access and download related employee resumes and project documentation

## How It Works
1. Text is extracted from PDFs and embedded using sentence transformers
2. User queries are vectorized and compared to the document index using FAISS
3. The most relevant document chunks are retrieved
4. LLMs (Llama3 or deepseek-r1) generate answers based on the retrieved context
5. Related project information, employee data, and document links are presented

## Development Notes
- The system uses semantic search rather than keyword matching for better results
- Multiple LLM models can be used depending on the query complexity
- The responses include a quality assessment from the deepseek model
