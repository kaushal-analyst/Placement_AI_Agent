import google.generativeai as genai
import json
import time
import random

def get_gemini_response(prompt, api_key):
    """Helper to get response from Gemini with retry logic."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    max_retries = 3
    base_delay = 10
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return None # Return None to trigger fallback
            else:
                return f"Error: {str(e)}"
    return None

def parse_resume_with_ai(resume_text, api_key):
    """Extracts Job Role and Skills from resume text."""
    # Truncate to 1000 characters to save tokens on the free tier
    truncated_resume = resume_text[:1000] 
    
    prompt = f"""
    Analyze the following resume text and extract the 'Job Role' (e.g., Python Developer, Data Scientist) and a list of 'Key Skills'.
    Return the result in JSON format like this:
    {{
        "role": "extracted role",
        "skills": ["skill1", "skill2", "skill3"]
    }}
    
    Resume Text:
    {truncated_resume}
    """
    try:
        response_text = get_gemini_response(prompt, api_key)
        # Clean up json string if it has backticks
        response_text = response_text.replace("```json", "").replace("```", "")
        return json.loads(response_text)
    except Exception as e:
        return {"role": "Unknown", "skills": [], "error": str(e)}

def simulate_job_discovery(role, location):
    """Simulates finding jobs based on role and location."""
    # In a real app, this would scrape LinkedIn/Indeeb or use an API.
    # For this assignment, we simulate it.
    
    companies = ["TechCorp Solutions", "InnovateX", "DataStream Inc.", "CloudNet Systems", "AlphaWave AI"]
    jobs = []
    
    for _ in range(3): # Simulate finding 3 jobs
        company = random.choice(companies)
        companies.remove(company) # Avoid duplicates
        jobs.append({
            "company": company,
            "role": role,
            "location": location,
            "hr_email": f"hr@{company.lower().replace(' ', '')}.com", # Simulated HR email
            "status": "Found"
        })
    return jobs

def generate_cover_letter(resume_text, job_description, api_key):
    """Generates a personalized cover letter."""
    prompt = f"""
    Write a professional and personalized cover letter for the position of {job_description['role']} at {job_description['company']}.
    Use the candidate's skills from the resume text below.
    Keep it concise (max 200 words).
    
    Resume Context:
    {resume_text[:1000]}
    """
    response = get_gemini_response(prompt, api_key)
    
    if not response:
        # Fallback Cover Letter
        return f"""
Dear Hiring Manager,

I am writing to express my strong interest in the {job_description['role']} position at {job_description['company']}. 

With my background and skills extracted from my resume, I am confident in my ability to contribute effectively to your team. I am eager to apply my technical expertise to help {job_description['company']} achieve its goals.

Thank you for considering my application. I look forward to the possibility of discussing how my skills align with the needs of your team.

Sincerely,
Job Applicant
(Generated via Fallback Mode due to AI Rate Limit)
        """
    return response

def generate_interview_questions(role, api_key):
    """Generates interview questions for the role."""
    prompt = f"""
    Generate a list of 10 technical and behavioral interview questions for a {role} position.
    Return them as a numbered list.
    """
    response = get_gemini_response(prompt, api_key)
    
    if not response:
        # Fallback Questions
        return """
**Rate Limit Reached. Here are some standard interview questions:**

1. Tell me about yourself and your background.
2. Why are you interested in this role?
3. What are your greatest strengths and weaknesses?
4. Describe a challenging project you worked on and how you handled it.
5. Where do you see yourself in 5 years?
6. How do you handle tight deadlines?
7. Describe a time you had a conflict with a colleague.
8. What is your preferred work style?
9. Do you have any questions for us?
10. (Technical: Be prepared to discuss specific skills mentioned in your resume).
        """
    return response
