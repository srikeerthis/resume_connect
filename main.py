import streamlit as st
from pymongo import MongoClient
from PyPDF2 import PdfReader
from bson import Binary

# Connect to MongoDB
client = MongoClient('localhost:27017')  # Replace with your MongoDB connection string
db = client['hired_db']  # Database
collection = db['resumes']  # Collection

# Helper function to extract text from resume (PDF)
def extract_resume_text(uploaded_file):
    if uploaded_file is not None:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    return None

# Streamlit UI
st.title('Hired Simple Version')
st.subheader('Submit your Resume and Answer Questions')

# Candidate Info
candidate_name = st.text_input('Name')
candidate_email = st.text_input('Email')

# Resume Upload
uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

# Extract resume text and display it
resume_text = extract_resume_text(uploaded_file)
if resume_text:
    st.text_area("Extracted Resume Text", resume_text, height=200)

# Questions
st.subheader("Please answer the following questions:")
question1 = st.text_input("What is your main technical skill?")
question2 = st.text_input("Why do you want to join our company?")
question3 = st.text_input("Where do you see yourself in 5 years?")

# Submit button
if st.button('Submit'):
    if candidate_name and candidate_email and uploaded_file and question1 and question2 and question3:
        # Convert uploaded resume to binary
        resume_binary = Binary(uploaded_file.read())

        # Create document for MongoDB
        resume_data = {
            "candidate_name": candidate_name,
            "email": candidate_email,
            "resume": resume_binary,  # Store resume as binary
            "answers": {
                "question1": question1,
                "question2": question2,
                "question3": question3
            }
        }

        # Insert into MongoDB
        collection.insert_one(resume_data)
        
        st.success("Your resume and answers have been submitted successfully!")
    else:
        st.error("Please fill in all the fields and upload a resume.")
