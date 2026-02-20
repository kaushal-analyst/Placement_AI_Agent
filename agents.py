import google.generativeai as genai
import json
import time
import random
import requests

def get_gemini_response(prompt, api_key):
    """Helper to get response from Gemini with retry logic."""
    genai.configure(api_key=api_key)
    # Using flash-lite to minimize quota usage
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
                    return None  # Return None to trigger fallback
            else:
                return f"Error: {str(e)}"
    return None

def parse_resume_with_ai(resume_text, api_key):
    """Extracts Job Role and Skills from resume text."""
    # Truncate to 800 characters to save tokens on the free tier
    truncated_resume = resume_text[:800]
    
    prompt = f"""
    Analyze the following resume text and extract the 'Job Role' (e.g., Python Developer, Data Scientist) and a list of 'Key Skills'.
    Return ONLY valid JSON format like this:
    {{
        "role": "extracted role",
        "skills": ["skill1", "skill2", "skill3"]
    }}
    
    Resume Text:
    {truncated_resume}
    """
    try:
        response_text = get_gemini_response(prompt, api_key)
        if not response_text:
            return {"role": "Software Developer", "skills": ["Python"]}
        # Clean up json string if it has backticks
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception as e:
        return {"role": "Software Developer", "skills": [], "error": str(e)}

def search_jobs_jsearch(role, location, rapidapi_key, num_results=3):
    """
    Fetches real job listings from JSearch API (RapidAPI).
    Free tier: 200 requests/month.
    Returns a list of job dicts or empty list on failure.
    """
    url = "https://jsearch.p.rapidapi.com/search"
    
    querystring = {
        "query": f"{role} in {location}",
        "page": "1",
        "num_pages": "1",
        "date_posted": "week"
    }
    
    headers = {
        "x-rapidapi-host": "jsearch.p.rapidapi.com",
        "x-rapidapi-key": rapidapi_key
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        jobs = []
        for item in data.get("data", [])[:num_results]:
            # Extract relevant fields
            company = item.get("employer_name", "Unknown Company")
            job_title = item.get("job_title", role)
            job_location = item.get("job_city", location) or location
            
            # Extract job description (truncate to save Gemini tokens later)
            job_description = item.get("job_description", "")[:800]
            
            # Try to get apply email or HR email from the listing
            apply_link = item.get("job_apply_link", "")
            employer_website = item.get("employer_website", "")
            
            # Construct a best-guess HR email from employer name / website
            domain = ""
            if employer_website:
                domain = employer_website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
            elif company:
                domain = company.lower().replace(" ", "").replace(",", "").replace(".", "") + ".com"
            
            hr_email = f"hr@{domain}" if domain else f"careers@{company.lower().replace(' ', '')}.com"
            
            jobs.append({
                "company": company,
                "role": job_title,
                "location": job_location,
                "hr_email": hr_email,
                "job_description": job_description,
                "apply_link": apply_link,
                "status": "Found"
            })
        
        return jobs
    except Exception as e:
        print(f"JSearch API error: {e}")
        return []

def simulate_job_discovery(role, location):
    """
    Fallback: Simulates finding jobs if no API key is available.
    """
    companies = ["TechCorp Solutions", "InnovateX", "DataStream Inc.", "CloudNet Systems", "AlphaWave AI"]
    random.shuffle(companies)
    jobs = []
    
    for company in companies[:3]:
        jobs.append({
            "company": company,
            "role": role,
            "location": location,
            "hr_email": f"hr@{company.lower().replace(' ', '').replace('.', '')}.com",
            "job_description": f"We are looking for a skilled {role} to join our team at {company} in {location}. "
                               f"The ideal candidate should have strong technical skills and experience in software development.",
            "apply_link": "",
            "status": "Found (Simulated)"
        })
    return jobs

def discover_jobs(role, location, rapidapi_key=""):
    """
    Main job discovery function.
    Uses JSearch API if RapidAPI key is available, else falls back to simulation.
    """
    if rapidapi_key and rapidapi_key.strip():
        jobs = search_jobs_jsearch(role, location, rapidapi_key, num_results=3)
        if jobs:
            return jobs, "real"
    
    # Fallback to simulation
    return simulate_job_discovery(role, location), "simulated"

def generate_cover_letter(resume_text, job, api_key):
    """Generates a personalized cover letter based on resume and job description."""
    job_description = job.get("job_description", "")
    company = job.get("company", "the company")
    role = job.get("role", "the position")
    
    prompt = f"""Write a professional and personalized cover letter for the following job.
Role: {role}
Company: {company}
Job Description: {job_description[:400]}

Candidate Resume (first 500 chars):
{resume_text[:500]}

Instructions:
- Be concise (max 180 words)
- Mention specific skills that match the job description
- Be professional and enthusiastic
- Do NOT use generic phrases like "I am writing to express"
"""
    response = get_gemini_response(prompt, api_key)
    
    if not response:
        # Fallback Cover Letter
        return f"""Dear Hiring Manager,

I am excited to apply for the {role} position at {company}. Based on my experience and skills outlined in my resume, I am confident I can make a meaningful contribution to your team.

My technical background aligns well with the requirements of this role. I am particularly drawn to {company}'s mission and believe my skills would be a strong match.

I look forward to the opportunity to discuss how I can contribute. Thank you for your consideration.

Sincerely,
Applicant
(Note: Generated via Fallback Mode — Gemini API rate limit reached)
        """
    return response

def generate_interview_questions(role, resume_text, found_jobs, api_key):
    """
    Generates interview questions SPECIFIC to the actual job descriptions and resume.
    This ensures questions are relevant to the actual jobs applied to.
    """
    # Collect all job descriptions from actually applied jobs
    job_summaries = ""
    for i, job in enumerate(found_jobs[:3], 1):
        company = job.get("company", "Unknown")
        jd = job.get("job_description", "")[:300]
        job_summaries += f"\n{i}. {company} - {role}:\n{jd}\n"
    
    # Truncate resume for token efficiency
    resume_snippet = resume_text[:600]
    
    prompt = f"""You are an expert interview coach. Generate 10 targeted interview questions for a candidate who just applied to the following jobs.

JOBS APPLIED TO:
{job_summaries}

CANDIDATE RESUME (excerpt):
{resume_snippet}

Generate 10 specific interview questions that:
1. Match the technical skills required in the actual job descriptions above
2. Reference the candidate's actual experience from their resume
3. Include both technical and behavioral questions
4. Are specific — not generic

Format as a numbered list. Each question should be on its own line.
"""
    response = get_gemini_response(prompt, api_key)
    
    if not response:
        # Fallback — Role-specific at least
        return f"""**Standard Interview Questions for {role}** *(Gemini API rate limit reached)*

1. Walk me through your experience as a {role}.
2. What tools and technologies do you use daily in your work as a {role}?
3. Describe a challenging project you completed — what was your role and what did you learn?
4. How do you stay up-to-date with the latest trends in your field?
5. Describe a situation where you had to debug a difficult problem under pressure.
6. How do you approach working in a team with different skill sets?
7. Tell me about a time you disagreed with a technical decision — how was it resolved?
8. What is your experience with code review and best practices?
9. How do you handle multiple competing deadlines?
10. Do you have any questions for the team about the role or company culture?
        """
    return response
