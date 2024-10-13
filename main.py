import streamlit as st
from pymongo import MongoClient
from PyPDF2 import PdfReader
from bson import Binary
from openai import OpenAI
import os
import dotenv
import hashlib
from streamlit.components.v1 import html


# html(
#     '<img src="dino.jpg" alt="Description of the image" />'
# )

dotenv.load_dotenv()
# Set up OpenAI API key
openai_key = os.getenv("OPENAI_API_KEY")
openai_prompt = os.getenv("OPENAI_PROMPT")

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

# Function for analyzing resume using OpenAI
def analyze_resume(resume_text):
    openai_client = OpenAI()
    if resume_text:
        prompt = openai_prompt.format(resume_text=resume_text)
        
        # Call the OpenAI API
        completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that analyzes resumes."},
            {
                "role": "user",
                "content": prompt
            }
        ]
        )
        # Extract the analysis from OpenAI's response
        return completion.choices[0].message.content
    
    return "No resume text provided for analysis."

# Function to calculate hash of a file to detect changes
def hash_file(file):
    hasher = hashlib.md5()
    hasher.update(file.read())
    return hasher.hexdigest()

# Streamlit UI
st.title('Hired Simple Version')

st.markdown("""
    <style>
    body {
        background-color: #1A0800;
        color: #E8E8E8;
    }
    .stAppHeader{
        background-color: #2BFF00
                }
    .st-emotion-cache-1r4qj8v{
        background-color: #1A0800;    
            }        
    .st-emotion-cache-ue6h4q {
        color: #2BFF00;
                    }
            .st-emotion-cache-12h5x7g.e1nzilvr5{
            color: white;}
    h1, h2, h3, h4, .st-emotion-cache-12h5x7g{
        color: #2BFF00;
    }
    .stTextInput, .stTextArea, .stFileUploader {
        background-color: #2C3E50;
        color: #ECF0F1;
        border: 1px solid #2BFF00;
        padding: 10px;
        border-radius: 5px;
    }
    .stButton button {
        background-color: #E74C3C;
        color: #FFF;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        transition: background-color 0.3s ease;
    }
    .stButton button:hover {
        background-color: #C0392B;
    }
    .stRadio > div {
        color: #E8E8E8;
    }
            
    .stSidebar{
        background-color: #424242;
            }
    .sidebar .sidebar-content {
        background-color: #2BFF00;
        color: #ECF0F1;
    }
    .sidebar .sidebar-content .stRadio {
        color: #ECF0F1;
    }
    .stAlert {
        background-color: #27AE60;
        color: white;
    }
    .stTextInput > div, .stFileUploader > div {
        color: #FFF;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar for selecting user type
user_type = st.sidebar.radio("Are you a:", ("Candidate", "Recruiter"))

### Candidate Session ###
if user_type == "Candidate":

    st.subheader('Submit your Resume and Answer Questions')

    # Candidate Info
    candidate_name = st.text_input('Name')
    candidate_email = st.text_input('Email')

    # Resume Upload
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

    # Use session state to store the analysis result so that it only happens once when the resume is uploaded
    if "analysis" not in st.session_state:
        st.session_state.analysis = None
        st.session_state.resume_hash = None

    # If a resume is uploaded, calculate its hash
    if uploaded_file:
        current_resume_hash = hash_file(uploaded_file)

        # Reanalyze if the resume has changed
        if current_resume_hash != st.session_state.resume_hash:
            st.session_state.resume_hash = current_resume_hash  # Update hash in session state
            uploaded_file.seek(0)  # Reset file pointer after hashing
            resume_text = extract_resume_text(uploaded_file)
            
            if resume_text:
                analysis = analyze_resume(resume_text)
                st.session_state.analysis = analysis
        else:
            st.success("Resume unchanged, no reanalysis needed.")

    # # Resume Analysis - only perform if it's the first time or the resume is re-uploaded
    # if uploaded_file and resume_text and st.session_state.analysis is None:
    #     analysis = analyze_resume(resume_text)
    #     st.session_state.analysis = analysis

    # Display the analysis in a non-editable text area
    if st.session_state.analysis:
        st.text_area("Resume Analysis", st.session_state.analysis, height=200, disabled=True)

    # Questions
    st.subheader("Please answer the following questions:")
    question1 = st.text_input("Do you require sponsorship to work in the US?")
    question2 = st.text_input("Are you currently in the USA")
    question3 = st.text_input("What is your expected salary range?")

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
                },
                "analysis": st.session_state.analysis  # Store the analysis generated by OpenAI
            }

            # Insert into MongoDB
            collection.insert_one(resume_data)
            
            st.success("Your resume and answers have been submitted successfully!")
        else:
            st.error("Please fill in all the fields and upload a resume.")

### Recruiter Session ###
elif user_type == "Recruiter":
    st.header("Search for Resumes")

    # Search input
    search_term = st.text_input("Search by candidate name, email, or keyword in analysis")

    # Search button
    if st.button("Search"):
        # Query the MongoDB collection based on search term
        query = {
            "$or": [
                {"candidate_name": {"$regex": search_term, "$options": "i"}},
                {"email": {"$regex": search_term, "$options": "i"}},
                {"analysis": {"$regex": search_term, "$options": "i"}}
            ]
        }
        results = list(collection.find(query))

        if results:
            st.write(f"Found {len(results)} results:")
            for result in results:
                st.subheader(f"Candidate: {result['candidate_name']}")
                st.write(f"Email: {result['email']}")
                st.write(f"Analysis: {result['analysis']}")
                st.write(f"Q1: {result['answers']['question1']}")
                st.write(f"Q2: {result['answers']['question2']}")
                st.write(f"Q3: {result['answers']['question3']}")
                st.write("---")
        else:
            st.write("No results found for your search term.")
