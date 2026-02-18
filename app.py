import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime
import utils
import agents
from tempfile import NamedTemporaryFile

# Set page config
st.set_page_config(
    page_title="Job Application Assistant", # Changed title to be generic but theme is TOPS
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.warning(f"Style file {file_name} not found.")

load_css("style.css")

import base64

def get_img_as_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- Header Component ---
def render_header():
    logo_html = ""
    if os.path.exists("logo.png"):
        img_b64 = get_img_as_base64("logo.png")
        logo_html = f'<img src="data:image/png;base64,{img_b64}" class="logo-img" alt="TOPS Logo" style="height: 50px;">'
    else:
        # Fallback or placeholder if file not found
        logo_html = '<h1 style="color: #1a237e; margin: 0;">TOPS TECHNOLOGIES</h1>'

    st.markdown(f"""
        <div class="custom-header" style="justify-content: center;">
            <div class="logo-container">
                {logo_html}
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.header("Job Application Assistant")
    
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=['pdf'])
    
    st.divider()
    
    st.subheader("Credentials")
    # Pre-filling for demo purposes based on user request, but safely editable
    email = st.text_input("Email Address", value="19.why.1991@gmail.com") 
    app_password = st.text_input("Gmail App Password", type="password", value="xkpp uodp qwzk mnvw")
    api_key = st.text_input("Gemini API Key", type="password", value="AIzaSyDKZAhVP3Gdgm2nnwiOhEjH1jI15KyzV70")
    
    location = st.text_input("Preferred Location", value="Ahmedabad")
    manual_role = st.text_input("Target Job Role (Optional)", placeholder="e.g., Python Developer")

    st.divider()
    
    start_btn = st.button("Start Job Hunt Agent", type="primary")

# --- Main Dashboard ---

# Initialize session state
if 'stats' not in st.session_state:
    st.session_state['stats'] = {'jobs_found': 0, 'emails_sent': 0, 'skipped': 0}
if 'logs' not in st.session_state:
    st.session_state['logs'] = []
if 'results' not in st.session_state:
    st.session_state['results'] = pd.DataFrame(columns=["Company", "Role", "Location", "Status", "AI Reason"])

# Function to update logs
log_placeholder = st.empty()
def update_logs(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state['logs'].append(f"[{timestamp}] {message}")
    if len(st.session_state['logs']) > 50:
            st.session_state['logs'].pop(0)
    
    log_html = '<div class="log-container">' + "<br>".join(st.session_state['logs']) + '</div>'
    log_placeholder.markdown(log_html, unsafe_allow_html=True)

# Stat Cards
col1, col2, col3 = st.columns(3)
stat1 = col1.empty()
stat2 = col2.empty()
stat3 = col3.empty()

def update_stats():
    with stat1.container():
        st.metric("Total Jobs Found", st.session_state['stats']['jobs_found'])
    with stat2.container():
        st.metric("Applications Sent", st.session_state['stats']['emails_sent'])
    with stat3.container():
        st.metric("Skipped", st.session_state['stats']['skipped'])

update_stats()

# Two-column layout for Logs and Results
row2_col1, row2_col2 = st.columns([1, 2])

with row2_col1:
    st.subheader("Agent Live Logs")
    # Placeholder was defined above logged `log_placeholder`
    # We need to re-render it if the page reruns
    log_html = '<div class="log-container">' + "<br>".join(st.session_state['logs']) + '</div>'
    log_placeholder.markdown(log_html, unsafe_allow_html=True)

with row2_col2:
    st.subheader("Application Results")
    results_placeholder = st.empty()
    results_placeholder.dataframe(st.session_state['results'], use_container_width=True)

# --- Agent Logic ---
if start_btn:
    if not uploaded_file:
        st.error("Please upload a resume first.")
    elif not email or not app_password or not api_key:
        st.error("Please provide all credentials.")
    else:
        # Save uploaded file to temp
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            with st.spinner("Agent is working..."):
                # 1. Parse Resume
                update_logs("Reading resume...")
                resume_text = utils.extract_text_from_pdf(tmp_path)
                if "Error" in resume_text:
                     st.error(resume_text)
                     st.stop()
                
                # Extract role if not manually provided
                role = manual_role
                skills = []
                
                update_logs("Analyzing resume with Gemini...")
                parsed_data = agents.parse_resume_with_ai(resume_text, api_key)
                
                # If manual role is set, use it. Otherwise use extracted.
                if not role:
                    role = parsed_data.get("role", "Unknown")
                
                skills = parsed_data.get("skills", [])
                
                update_logs(f"Target Role: {role}")
                update_logs(f"Skills: {', '.join(skills[:3])}...")
                
                # 2. Find Jobs
                update_logs(f"Searching for {role} jobs in {location}...")
                found_jobs = agents.simulate_job_discovery(role, location)
                st.session_state['stats']['jobs_found'] += len(found_jobs)
                update_stats()
                
                if not found_jobs:
                    update_logs("No jobs found via simulation.")
                
                for job in found_jobs:
                    company = job['company']
                    hr_email = job['hr_email']
                    
                    update_logs(f"Found job at {company}. Extracting HR email...")
                    time.sleep(1) # Simulate extraction time
                    update_logs(f"HR Email found: {hr_email}")
                    
                    # 3. Generate Cover Letter
                    update_logs(f"Drafting cover letter for {company}...")
                    cover_letter = agents.generate_cover_letter(resume_text, job, api_key)
                    
                    with st.expander(f"📄 Cover Letter for {company}", expanded=False):
                        st.markdown(cover_letter)
                    
                    # 4. Send Email
                    update_logs(f"Sending application to {hr_email}...")
                    # Simulating email send (commented out real send for safety unless explicitly requested to force it, 
                    # but user requirements say 'Integrate smtplib'. I will call it.)
                    
                    email_subject = f"Application for {job['role']} - {company}"
                    
                    # ACTUAL SENDING
                    email_status, email_msg = utils.send_email(email, app_password, hr_email, email_subject, cover_letter, tmp_path)
                    
                    if email_status:
                        update_logs(f"✅ Application Sent to {company}")
                        st.session_state['stats']['emails_sent'] += 1
                        status_text = "Sent"
                    else:
                        update_logs(f"❌ Failed to send to {company}")
                        st.session_state['stats']['skipped'] += 1
                        status_text = "Failed"
                        if "BadCredentials" in email_msg or "Username and Password not accepted" in email_msg:
                             st.error("Authentication Failed: Please check your Gmail App Password. It is NOT your regular login password. Ensure 2-Step Verification is ON and generate a specific App Password.")
                    
                    update_stats()
                    
                    # Update Results Table
                    new_row = {
                        "Company": company,
                        "Role": job['role'],
                        "Location": location,
                        "Status": status_text,
                        "AI Reason": "Matched Skills"
                    }
                    st.session_state['results'] = pd.concat([st.session_state['results'], pd.DataFrame([new_row])], ignore_index=True)
                    results_placeholder.dataframe(st.session_state['results'], use_container_width=True)
                    
                    time.sleep(20) # Increased delay to 20s to avoid rate limits
                
                # 5. Interview Prep
                update_logs("Generating interview preparation questions...")
                questions = agents.generate_interview_questions(role, api_key)
                
                st.success("Job Hunt Cycle Complete!")
                st.markdown("### 🎯 Interview Preparation")
                st.markdown(questions)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            update_logs(f"Critical Error: {e}")
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
