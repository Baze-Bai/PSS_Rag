import pandas as pd
import os

# Define the paths for resumes and project PDFs
RESUMES_FOLDER = 'L:/Baze_project/Resumes' 
PROJECTS_FOLDER = 'L:/Baze_project/_Marketing Project Sheets' 
DATA_FILE = 'L:/Baze_project/Projects that Have been worked on in the last 8 years and the active employees.csv'  # Change to the actual file path

# Function to filter employees and hours based on project number
def get_filtered_data_by_projects(proj_numbers, df):
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
