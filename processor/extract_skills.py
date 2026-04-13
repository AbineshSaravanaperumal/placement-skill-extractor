import os
import sqlite3
import json
import time
from openai import OpenAI

print("PROCESSOR_MODULE: Loaded version 1.0.4 with role_filter support")

def get_db_path():
    """Returns absolute path to data/jobs.db using __file__."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "data", "jobs.db")

def get_api_key():
    """Returns OpenAI API key from Streamlit secrets or .env file."""
    try:
        import streamlit as st
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        from dotenv import load_dotenv
        import os
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
        )
        load_dotenv(env_path)
        return os.getenv("OPENAI_API_KEY")

def extract_skills_from_jd(description, client):
    """Calls OpenAI GPT-4o-mini to extract technical skills from job description."""
    if not description or description == "N/A":
        return []
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a technical recruiter. Extract only hard technical skills, tools, programming languages, and frameworks. Ignore soft skills."},
                {"role": "user", "content": f"Extract all technical skills from this job description. Return ONLY a valid JSON array of strings. No explanation, no markdown. Example: [\"Python\", \"SQL\", \"Tableau\"]\n\nJob Description:\n{description}"}
            ],
            max_tokens=300,
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        
        # Clean markdown formatting if present
        if content.startswith("```json"):
            content = content.replace("```json", "", 1).replace("```", "", 1).strip()
        elif content.startswith("```"):
            content = content.replace("```", "", 1).replace("```", "", 1).strip()
            
        return json.loads(content)
    except Exception as e:
        return []

def process_all_jobs(role_filter=None):
    """Processes jobs with missing skills and returns a flat list of skills for a specific role."""
    db_path = get_db_path()
    api_key = get_api_key()
    client = OpenAI(api_key=api_key)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    all_skills = []
    
    try:
        # 1. Processing missing skills (always do this across all jobs to keep DB healthy)
        cursor.execute("SELECT id, description FROM jobs WHERE extracted_skills IS NULL AND description IS NOT NULL")
        to_process = cursor.fetchall()
        
        for job_id, desc in to_process:
            skills = extract_skills_from_jd(desc, client)
            cursor.execute("UPDATE jobs SET extracted_skills = ? WHERE id = ?", (json.dumps(skills), job_id))
        
        conn.commit()
        
        # 2. Collect skills for the specific role requested
        if role_filter:
            cursor.execute("SELECT extracted_skills FROM jobs WHERE extracted_skills IS NOT NULL AND role = ?", (role_filter,))
        else:
            cursor.execute("SELECT extracted_skills FROM jobs WHERE extracted_skills IS NOT NULL")
            
        rows = cursor.fetchall()
        for row in rows:
            try:
                skills_list = json.loads(row[0])
                if isinstance(skills_list, list):
                    all_skills.extend(skills_list)
            except:
                continue
                
    except Exception as e:
        print(f"Error in processing: {e}")
    finally:
        conn.close()
        
    return all_skills

if __name__ == "__main__":
    skills = process_all_jobs()
    if skills:
        from collections import Counter
        top_10 = Counter(skills).most_common(10)
        print("\nTop 10 Extracted Skills:")
        for skill, count in top_10:
            print(f"- {skill}: {count}")
    else:
        print("No skills extracted or database empty.")
