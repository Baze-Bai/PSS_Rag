import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from Store_data import store_data
import os
import json
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from Find_project import get_filtered_data_by_projects, find_resumes
import re
import boto3

# === CONFIGURATION ===
REGION = "us-east-1"
MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

def ask_bedrock(prompt):
    """Call AWS Bedrock Claude model"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Create Bedrock client
        bedrock = boto3.client(
            'bedrock-runtime',
            region_name=REGION,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Prepare the request body for Claude
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.05
        }
        
        # Call Bedrock
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        if 'content' in response_body and len(response_body['content']) > 0:
            return response_body['content'][0]['text']
        else:
            return "Bedrock response format abnormal, answer content not found"
            
    except Exception as e:
        print(f"Error calling Bedrock: {str(e)}")
        return f"Error: {str(e)}"

def main():

    DATA_FILE = 'Baze_project/Projects that Have been worked on in the last 8 years and the active employees.csv'  # Change to the actual file path

    # Cache API key loading
    @st.cache_data
    def load_data():
        return pd.read_csv(DATA_FILE)

    # Cache data loading (assuming store_data() returns chunks and index)
    @st.cache_resource
    def load_chunks_and_index():
        return store_data()  # Returns chunks and index

    # Cache model loading
    @st.cache_resource
    def load_model():
        return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    st.set_page_config(page_title="Integrated RAG + Project Lookup", layout="wide")
    st.title("Integrated Q&A and Project Lookup")
    # Call the cached functions in the main logic
    df = load_data()
    chunks, index, file_names = load_chunks_and_index()
    model = load_model()

    # User question
    st.subheader("Ask a question")

    # 1. User inputs the question
    question = st.text_input("Enter your question here:")

    # Additional options such as temperature, top_k, etc., can be added as needed

    # 2. When the user clicks the button, trigger the RAG and streaming call
    if st.button("Ask"):
        if not question.strip():
            st.warning("Please enter a question.")
            return

        # Encode the question into a vector (and normalize)
        q_embedding = model.encode([question])
        q_embedding = np.array(q_embedding, dtype="float32")
        faiss.normalize_L2(q_embedding)

        # Search for the 5 text snippets most relevant to the question in FAISS
        k = 5
        D, I = index.search(q_embedding, k)  # D is the similarity scores, I are the indices
        top_idx = I[0]    # List of indices for the most relevant text snippets
        top_chunks = []
        top_file = []
        for idx in top_idx:  # I[0] is the list of top-k indices
            top_chunks.append(chunks[idx])
            top_file.append(file_names[idx])

        number_files = []
        for file in top_file:
            numbers = re.findall(r"\d+", file)
            number_files.append(numbers[0])
        
        unique_list = []
        for item in number_files:
            if item not in unique_list:
                unique_list.append(item)

        # Prepend '0' if your project IDs require that format
        project_numbers = ['0' + f for f in unique_list]
        
        if top_file:
            st.info(f"Found relevant projects: {', '.join(top_file)}")
        
        st.write("Answer")
        answer_container = st.empty()  # Container used for real-time answer updates
        answer_text = ""  # Cumulative answer content

        for i in range(5):
            context_text = top_chunks[i]
            prompt = f"Answer the user's questions based on the following documentation.\ndocument content:\n{context_text}\n\nquestion: {question}\n"

            response = ask_bedrock(prompt)
            
            answer_text += f"\n For File {top_file[i]} \n" + "\n"
            answer_text += response + '\n'
            
            answer_container.markdown(answer_text)

        st.subheader("Related Project Information")
        filtered_data = get_filtered_data_by_projects(project_numbers, df)
        
        # Display employee data
        if not filtered_data.empty:
            st.write("### Employees and Hours")
            st.dataframe(filtered_data)
        else:
            st.warning("No employees found for the given project numbers.")

        # Get resumes and project PDFs
        employees = filtered_data['Employee'].unique()
        resumes_found = find_resumes(employees)

        # Display resumes
        if resumes_found:
            st.write("### Employee Resumes")
            for emp, path in resumes_found.items():
                with open(path, "rb") as file:
                    st.download_button(label=f"Download {emp}'s Resume", data=file, file_name=f"{emp}.pdf")
        else:
            st.warning("No resumes found for the employees.")

        project_folder = 'Baze_project/_Marketing Project Sheets'

        project_pdfs_found = {}
        for file in top_file:
            project_pdfs_found[file] = os.path.join(project_folder, file+'.pdf')
        # Display project PDFs
        if project_pdfs_found:
            st.write("### Project PDFs")
            for f, path in project_pdfs_found.items():
                with open(path, "rb") as file:
                    st.download_button(label=f"Download Project {f} PDF", data=file, file_name=os.path.basename(path))
        else:
            st.warning("No project PDFs found for the given projects.")

if __name__ == "__main__":
    # To run locally: streamlit run Rag.py
    main()
