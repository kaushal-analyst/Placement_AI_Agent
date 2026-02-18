# Agentic AI Job Application Assistant

This is an AI-powered Job Application Assistant built with Streamlit, Google Gemini, and Python. It simulates searching for jobs based on your resume and location, generates tailored cover letters using generative AI, and automates email outreach.

## Features
- **Resume Parsing**: Extracts Job Role and Skills using AI.
- **Job Discovery (Simulated)**: Finds relevant jobs in your preferred location.
- **HR Extraction (Simulated)**: Identifies HR contacts.
- **Cover Letter Generation**: Creates personalized cover letters for each job.
- **Email Automation**: Sends applications directly via Gmail.
- **Interview Prep**: Generates custom interview questions based on the role.
- **Dashboard**: Track your application status in real-time.

## Prerequisites
- Python 3.8+
- Gmail Account with App Password enabled.
- Google Gemini API Key.

## Setup
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python -m streamlit run app.py
   ```

## Usage
1. Upload your Resume (PDF).
2. Enter your Credentials (Email, App Password, API Key) in the sidebar.
3. Click "Start Job Hunt Agent".
4. Watch the agent work in the "Agent Live Logs" panel.
5. View interview questions at the end of the process.

## Customization
- **Theme**: Currently styled to match TOPS Technologies (Navy & Sky Blue). To change, edit `style.css`.
- **Logic**: Modify `agents.py` to connect to real job search APIs or scrapers.

## Note
This is a prototype. Ensure you review the generated content before sending actual applications in a production environment.
