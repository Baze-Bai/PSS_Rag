import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from Store_data import store_data
import os
import requests
import json
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from Find_project import get_filtered_data_by_projects, find_resumes
import re
import ollama

def ask_ds(prompt):
    # Directly call the deepseek model using the ollama module
    try:
        # Call the generate method from the ollama library
        response = ollama.generate(
            model="deepseek-r1",  # Use the deepseek model
            prompt=prompt,
            options={
                "temperature": 0.15,
                "num_predict": 512  # Control the maximum token count
            }
        )
        
        print("Ollama response successfully received")
        
        # Extract content from the ollama response
        if response and 'response' in response:
            return response['response']
        else:
            return "Ollama response format abnormal, answer content not found"
            
    except Exception as e:
        print(f"Error calling Ollama: {str(e)}")
        return f"Error: {str(e)}"


def ask_ollama(prompt, model='llama3'):
    url = 'http://localhost:11434/api/generate'
    headers = {'Content-Type': 'application/json'}
    data = {
        'model': model,
        'prompt': prompt,
        'stream': False
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()['response']

def main():

    DATA_FILE = 'Baze_project/Projects that Have been worked on in the last 8 years and the active employees.csv'  # Change to the actual file path

    # Cache API key loading
    @st.cache_data
    def load_data():
        return pd.read_csv(DATA_FILE)
    
    @st.cache_data
    def get_bearer():
        load_dotenv()
        return 'Bearer ' + os.getenv("DEEP_SEEK_API_KEY")

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
    Bear = get_bearer()
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
    
    context_text = "\n".join(top_chunks)  # Join multiple text snippets with newlines

    prompt = f"Answer the user's questions based on the following documentation.\ndocument content:\n{context_text}\n\nquestion: {question}\n"

    st.write("Answer")
    answer_container = st.empty()  # Container used for real-time answer updates
    answer_text = ""  # Cumulative answer content

    for i in range(5):
        context_text = top_chunks[i]
        prompt = f"Answer the user's questions based on the following documentation.\ndocument content:\n{context_text}\n\nquestion: {question}\n"

        response = ollama.generate(
            model="Llama3",   # e.g., "llama3.2" or your custom model name
            prompt=prompt
        )
        
        answer_text += f"\n For File {top_file[i]} \n" + "\n"
        
        generated_text = response.get("response", "")
        answer_text += generated_text + '\n'
        
        answer_text += "\n LLM judge: \n" + "\n"

        judge_prompt = f"This is the question user ask:{prompt}; \n\nHere is the answer from LLM{generated_text}; \n\nplease judge the quality of the answer based on the question, rate the answer from 1~100, 100 represents best, while 1 represents worst, 100 represents best.."
        
        judge_text = ask_ds(judge_prompt)

        answer_text += judge_text + '\n'
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
    # To run locally: streamlit run app.py
    main()