import os
import sqlite3
import json
import time
from openai import OpenAI
import google.generativeai as genai

print("PROCESSOR_MODULE: Loaded version 1.0.6 with Robust Gemini Fallback")

def get_db_path():
    """Returns absolute path to data/jobs.db using __file__."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "data", "jobs.db")

def get_keys():
    """Returns both OpenAI and Gemini API keys from secrets or .env."""
    keys = {"openai": None, "gemini": None}
    try:
        import streamlit as st
        keys["openai"] = st.secrets.get("OPENAI_API_KEY")
        keys["gemini"] = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    
    if not keys["openai"] or not keys["gemini"]:
        from dotenv import load_dotenv
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
        )
        load_dotenv(env_path)
        keys["openai"] = keys["openai"] or os.getenv("OPENAI_API_KEY")
        keys["gemini"] = keys["gemini"] or os.getenv("GEMINI_API_KEY")
    
    return keys

def extract_skills_gemini(description, api_key):
    """Internal helper to extract skills using Google Gemini."""
    if not api_key:
        return []
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""You are a technical recruiter. Extract only hard technical skills, tools, programming languages, and frameworks.
Ignore soft skills. Return ONLY a valid JSON array of strings. No explanation, no markdown. 

Job Description:
{description}"""

        response = model.generate_content(prompt)
        content = response.text.strip()
        # Clean markdown
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        print(f"Gemini fallback error: {e}")
        return []

def extract_skills_from_jd(description, openai_client, gemini_key):
    """Extract skills using OpenAI with a fallback to Gemini if needed."""
    if not description or len(description.strip()) < 10:
        return []

    # 1. Try OpenAI first
    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=300,
                temperature=0,
                messages=[
                    {"role": "system", "content": "You are a technical recruiter. Extract only hard technical skills. Return ONLY a JSON array."},
                    {"role": "user", "content": f"Extract technical skills from:\n{description}"}
                ]
            )
            raw = response.choices[0].message.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            skills = json.loads(raw)
            if isinstance(skills, list):
                return [s for s in skills if isinstance(s, str) and len(s) > 1]
        except Exception as e:
            err = str(e).lower()
            if "quota" in err or "429" in err or "billing" in err:
                print("OpenAI Quota reached. Switching to Gemini Fallback...")
            else:
                print(f"OpenAI error: {e}")

    # 2. Fallback to Gemini if OpenAI failed or is not configured
    return extract_skills_gemini(description, gemini_key)

def process_all_jobs(role_filter=None):
    """Processes jobs with missing skills and returns a flat list of skills for a specific role."""
    db_path = get_db_path()
    keys = get_keys()
    
    openai_client = OpenAI(api_key=keys["openai"]) if keys["openai"] else None
    gemini_key = keys["gemini"]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    all_skills = []
    
    try:
        # 1. Processing missing skills
        cursor.execute("SELECT id, description FROM jobs WHERE extracted_skills IS NULL AND description IS NOT NULL")
        to_process = cursor.fetchall()
        
        if to_process:
            print(f"Processing skills for {len(to_process)} jobs...")
            for job_id, desc in to_process:
                skills = extract_skills_from_jd(desc, openai_client, gemini_key)
                if isinstance(skills, list) and skills:
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
