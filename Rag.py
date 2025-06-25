"""
Enhanced PSS RAG System with AWS Bedrock Integration
Implements comprehensive security, monitoring, and error handling.
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from Store_data import store_data
import os
import streamlit as st
import pandas as pd
from Find_project import get_filtered_data_by_projects, find_resumes
import re
import time
from datetime import datetime

# Import our enhanced modules
from config import Config
from utils.logger import logger
from utils.security import security_manager
from services.llm_service import llm_service

class RAGSystem:
    """Enhanced RAG System with comprehensive features"""
    
    def __init__(self):
        self.chunks = None
        self.index = None
        self.file_names = None
        self.model = None
        self.df = None
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the RAG system with proper error handling"""
        try:
            logger.info("Initializing PSS RAG System...")
            
            # Validate configuration
            config_validation = Config.validate_config()
            if not config_validation["is_valid"]:
                st.error(f"Configuration Error: {', '.join(config_validation['missing_required'])}")
                st.stop()
            
            # Log warnings
            for warning in config_validation["warnings"]:
                logger.warning(warning)
                st.warning(warning)
            
            # Initialize session state
            if 'session_start' not in st.session_state:
                st.session_state.session_start = datetime.now()
            
            logger.info("System initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {str(e)}")
            st.error(f"System initialization failed: {str(e)}")
            st.stop()
    
    @st.cache_data
    def load_data(_self):
        """Load project data with caching"""
        try:
            return pd.read_csv(Config.DATA_FILE)
        except Exception as e:
            logger.error(f"Failed to load data file: {str(e)}")
            raise
    
    @st.cache_resource
    def load_chunks_and_index(_self):
        """Load chunks and FAISS index with caching"""
        try:
            return store_data()
        except Exception as e:
            logger.error(f"Failed to load chunks and index: {str(e)}")
            raise
    
    @st.cache_resource
    def load_embedding_model(_self):
        """Load embedding model with caching"""
        try:
            return SentenceTransformer(Config.EMBEDDING_MODEL)
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise
    
    def setup_ui(self):
        """Setup Streamlit UI"""
        st.set_page_config(
            page_title="PSS RAG System", 
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("🔍 PSS Professional Services RAG System")
        st.markdown("*AI-powered project and employee information retrieval*")
        
        # Sidebar with system information
        with st.sidebar:
            st.header("System Status")
            
            # Health check
            health = llm_service.health_check()
            if health["healthy"]:
                st.success("✅ LLM Service: Healthy")
            else:
                st.error("❌ LLM Service: Unhealthy")
            
            # Performance stats
            stats = llm_service.get_performance_stats()
            st.metric("Total Requests", stats["total_requests"])
            st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
            st.metric("Avg Response Time", f"{stats['average_response_time']:.2f}s")
            
            # Security info
            session_info = security_manager.get_session_info()
            st.metric("Rate Limit Remaining", session_info["rate_limit_remaining"])
            
            # Configuration display
            with st.expander("Configuration"):
                st.text(f"Model: {Config.AWS_MODEL_ID}")
                st.text(f"Region: {Config.AWS_REGION}")
                st.text(f"Max Tokens: {Config.MAX_TOKENS}")
                st.text(f"Temperature: {Config.LLM_TEMPERATURE}")
    
    def process_query(self, question: str) -> tuple:
        """Process user query and return results"""
        try:
            # Security validation
            client_id = security_manager.get_client_ip()
            allowed, remaining = security_manager.check_rate_limit(client_id)
            
            if not allowed:
                st.error("⚠️ Rate limit exceeded. Please wait before making another request.")
                return None, None, None
            
            # Encode the question into a vector
            q_embedding = self.model.encode([question])
            q_embedding = np.array(q_embedding, dtype="float32")
            faiss.normalize_L2(q_embedding)
            
            # Search for relevant chunks
            k = Config.TOP_K_RESULTS
            D, I = self.index.search(q_embedding, k)
            top_idx = I[0]
            
            top_chunks = []
            top_files = []
            
            for idx in top_idx:
                top_chunks.append(self.chunks[idx])
                top_files.append(self.file_names[idx])
            
            # Extract project numbers
            number_files = []
            for file in top_files:
                numbers = re.findall(r"\d+", file)
                if numbers:
                    number_files.append(numbers[0])
            
            unique_list = list(set(number_files))
            project_numbers = ['0' + f for f in unique_list]
            
            return top_chunks, top_files, project_numbers
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            st.error(f"Error processing query: {str(e)}")
            return None, None, None
    
    def generate_answers(self, question: str, top_chunks: list, top_files: list) -> str:
        """Generate answers using LLM service"""
        answer_text = ""
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, (chunk, file_name) in enumerate(zip(top_chunks, top_files)):
            try:
                progress = (i + 1) / len(top_chunks)
                progress_bar.progress(progress)
                status_text.text(f"Processing file {i+1}/{len(top_chunks)}: {file_name}")
                
                # Generate response using LLM service
                response = llm_service.generate_response(question, chunk)
                
                answer_text += f"\n### 📄 File: {file_name}\n\n"
                
                if response["success"]:
                    answer_text += response["response"] + "\n\n"
                    answer_text += f"*Response time: {response['response_time']:.2f}s*\n\n"
                else:
                    answer_text += f"❌ Error: {response['error']}\n\n"
                    logger.error(f"LLM response error for file {file_name}: {response['error']}")
                
                # Add separator
                answer_text += "---\n\n"
                
            except Exception as e:
                logger.error(f"Error generating answer for file {file_name}: {str(e)}")
                answer_text += f"❌ Error processing {file_name}: {str(e)}\n\n"
        
        progress_bar.empty()
        status_text.empty()
        
        return answer_text
    
    def display_project_info(self, project_numbers: list):
        """Display project and employee information"""
        if not project_numbers:
            return
        
        st.subheader("📊 Related Project Information")
        
        try:
            filtered_data = get_filtered_data_by_projects(project_numbers, self.df)
            
            if not filtered_data.empty:
                st.write("### 👥 Employees and Hours")
                st.dataframe(
                    filtered_data,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Employee resumes
                employees = filtered_data['Employee'].unique()
                resumes_found = find_resumes(employees)
                
                if resumes_found:
                    st.write("### 📄 Employee Resumes")
                    cols = st.columns(min(len(resumes_found), 4))
                    
                    for idx, (emp, path) in enumerate(resumes_found.items()):
                        with cols[idx % 4]:
                            try:
                                with open(path, "rb") as file:
                                    st.download_button(
                                        label=f"📄 {emp}",
                                        data=file,
                                        file_name=f"{emp}_Resume.docx",
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                    )
                            except Exception as e:
                                st.error(f"Error loading resume for {emp}: {str(e)}")
                
                # Project PDFs
                project_folder = Config.PROJECTS_FOLDER
                project_pdfs_found = {}
                
                for file_name in set([f.split('.')[0] for f in os.listdir(project_folder) if f.endswith('.pdf')]):
                    project_pdfs_found[file_name] = os.path.join(project_folder, f"{file_name}.pdf")
                
                if project_pdfs_found:
                    st.write("### 📋 Project Documents")
                    cols = st.columns(min(len(project_pdfs_found), 4))
                    
                    for idx, (proj, path) in enumerate(project_pdfs_found.items()):
                        with cols[idx % 4]:
                            try:
                                with open(path, "rb") as file:
                                    st.download_button(
                                        label=f"📋 {proj}",
                                        data=file,
                                        file_name=os.path.basename(path),
                                        mime="application/pdf"
                                    )
                            except Exception as e:
                                st.error(f"Error loading project {proj}: {str(e)}")
            else:
                st.warning("No employees found for the given project numbers.")
                
        except Exception as e:
            logger.error(f"Error displaying project info: {str(e)}")
            st.error(f"Error loading project information: {str(e)}")
    
    def run(self):
        """Main application loop"""
        try:
            # Setup UI
            self.setup_ui()
            
            # Load data
            with st.spinner("🔄 Loading system components..."):
                self.df = self.load_data()
                self.chunks, self.index, self.file_names = self.load_chunks_and_index()
                self.model = self.load_embedding_model()
            
            st.success("✅ System ready!")
            
            # Main query interface
            st.subheader("💭 Ask a Question")
            
            with st.form("query_form"):
                question = st.text_area(
                    "Enter your question here:",
                    height=100,
                    max_chars=Config.MAX_QUERY_LENGTH,
                    help=f"Maximum {Config.MAX_QUERY_LENGTH} characters"
                )
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    submit_button = st.form_submit_button("🔍 Ask", use_container_width=True)
                with col2:
                    if st.form_submit_button("🧹 Clear", use_container_width=True):
                        st.rerun()
            
            # Process query
            if submit_button and question.strip():
                start_time = time.time()
                
                with st.spinner("🔍 Searching relevant documents..."):
                    top_chunks, top_files, project_numbers = self.process_query(question)
                
                if top_chunks:
                    st.info(f"📁 Found relevant projects: {', '.join(set(top_files))}")
                    
                    st.subheader("🤖 AI Analysis")
                    answer_container = st.empty()
                    
                    with st.spinner("🧠 Generating AI responses..."):
                        answer_text = self.generate_answers(question, top_chunks, top_files)
                    
                    answer_container.markdown(answer_text)
                    
                    # Display project information
                    self.display_project_info(project_numbers)
                    
                    total_time = time.time() - start_time
                    st.success(f"✅ Query completed in {total_time:.2f} seconds")
                
                else:
                    st.error("❌ No relevant documents found or query processing failed.")
            
            elif submit_button:
                st.warning("⚠️ Please enter a question.")
                
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            st.error(f"Application error: {str(e)}")

def main():
    """Main function"""
    try:
        rag_system = RAGSystem()
        rag_system.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        st.error(f"Fatal system error: {str(e)}")

if __name__ == "__main__":
    main()
