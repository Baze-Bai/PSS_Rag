import pandas as pd
import streamlit as st
import os

# Define the paths for resumes and project PDFs
RESUMES_FOLDER = 'L:/Baze_project/Resumes' 
PROJECTS_FOLDER = 'L:/Baze_project/_Marketing Project Sheets' 
DATA_FILE = 'L:/Baze_project/Projects that Have been worked on in the last 8 years and the active employees.csv'  # Change to the actual file path

# Load the data
@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE)

df = load_data()

# Function to filter employees and hours based on project number
def get_filtered_data_by_projects(proj_numbers):
    filtered_df = df[df['Proj Cd'].isin(proj_numbers)][['Employee', 'Proj Cd', 'Hrs']]
    filtered_df.columns = ['Employee', 'Project Number', 'Hours']
    return filtered_df

# Function to find resumes
def find_resumes(employees):
    resumes = {}
    for emp in employees:
        resume_path = os.path.join(RESUMES_FOLDER, f"{emp}.docx")
        if os.path.exists(resume_path):
            resumes[emp] = resume_path
    return resumes

# Function to find project PDFs
def find_project_pdfs(proj_numbers):
    for i in range(len(proj_numbers)):
        proj_numbers[i] = proj_numbers[i][1:]
    project_pdfs = {} 
    for proj in proj_numbers:
        for file in os.listdir(PROJECTS_FOLDER):
            if file.startswith(str(proj)) and file.endswith(".pdf"):
                project_pdfs[file] = os.path.join(PROJECTS_FOLDER, file)
    return project_pdfs

# Streamlit UI
st.title("Project Employee Lookup")

# User inputs project numbers
project_numbers_input = st.text_input("Enter project numbers separated by commas:")


if st.button("Search"):
    if project_numbers_input:
        project_numbers = ['0' + num.strip() for num in project_numbers_input.split(",")]

        # Get employee details
        filtered_data = get_filtered_data_by_projects(project_numbers)

        # Display employee data
        if not filtered_data.empty:
            st.write("### Employees and Hours")
            st.dataframe(filtered_data)
        else:
            st.warning("No employees found for the given project numbers.")

        # Get resumes and project PDFs
        employees = filtered_data['Employee'].unique()
        resumes_found = find_resumes(employees)
        project_pdfs_found = find_project_pdfs(project_numbers)

        # Display resumes
        if resumes_found:
            st.write("### Employee Resumes")
            for emp, path in resumes_found.items():
                with open(path, "rb") as file:
                    st.download_button(label=f"Download {emp}'s Resume", data=file, file_name=f"{emp}.pdf")
        else:
            st.warning("No resumes found for the employees.")

        # Display project PDFs
        if project_pdfs_found:
            st.write("### Project PDFs")
            for f, path in project_pdfs_found.items():
                with open(path, "rb") as file:
                    st.download_button(label=f"Download Project {f} PDF", data=file, file_name=os.path.basename(path))
        else:
            st.warning("No project PDFs found for the given projects.")
