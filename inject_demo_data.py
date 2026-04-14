import json
import os

def get_demo_jobs(role, location):
    """Returns a list of realistic demo jobs with pre-extracted skills."""
    
    # Pre-defined skills for each role
    templates = {
        "Data Analyst": [
            {"title": "Senior Data Analyst", "description": "Expert in Python, SQL and Tableau.", "salary": "12-18 Lacs", "skills": ["Python", "SQL", "Tableau", "AWS"]},
            {"title": "Junior Analyst", "description": "Requires SQL, Power BI and Excel.", "salary": "6-10 Lacs", "skills": ["SQL", "Power BI", "Excel"]},
            {"title": "BI Developer", "description": "Mastery in Power BI and Snowflake.", "salary": "10-15 Lacs", "skills": ["Power BI", "SQL", "Snowflake"]}
        ],
        "Data Scientist": [
            {"title": "Staff Data Scientist", "description": "ML, TensorFlow, and Python skills.", "salary": "25-45 Lacs", "skills": ["Python", "Machine Learning", "TensorFlow", "Statistics"]},
            {"title": "AI Researcher", "description": "PyTorch, NLP, and Deep Learning.", "salary": "30-50 Lacs", "skills": ["PyTorch", "NLP", "Deep Learning", "Python"]},
            {"title": "ML Associate", "description": "Scikit-Learn, Pandas and data cleaning.", "salary": "12-20 Lacs", "skills": ["Python", "Scikit-Learn", "Pandas"]}
        ],
        "ML Engineer": [
            {"title": "MLOps Engineer", "description": "Kubernetes, Docker, and FastAPI.", "salary": "20-35 Lacs", "skills": ["Kubernetes", "Docker", "FastAPI", "Python"]},
            {"title": "Machine Learning Engineer", "description": "Spark, TensorFlow and Big Data.", "salary": "18-30 Lacs", "skills": ["Spark", "TensorFlow", "Big Data", "Python"]},
            {"title": "Computer Vision Engineer", "description": "OpenCV, PyTorch and image processing.", "salary": "22-40 Lacs", "skills": ["OpenCV", "PyTorch", "Python"]}
        ],
        "Business Analyst": [
            {"title": "Product Business Analyst", "description": "Stakeholders, Jira, and SQL.", "salary": "10-18 Lacs", "skills": ["SQL", "Jira", "Agile", "Stakeholder Management"]},
            {"title": "Sr. Business Analyst", "description": "Advanced Excel, Tableau and Agile.", "salary": "15-25 Lacs", "skills": ["Excel", "Tableau", "Agile", "SQL"]},
            {"title": "Market Data Analyst", "description": "SQL, R and Power BI.", "salary": "12-20 Lacs", "skills": ["SQL", "R", "Power BI"]}
        ],
        "Software Developer": [
            {"title": "Full Stack Developer (Next.js)", "description": "React, Node.js and TypeScript.", "salary": "15-30 Lacs", "skills": ["React", "Node.js", "TypeScript", "Next.js"]},
            {"title": "Backend Software Engineer", "description": "Python FastAPI, PostgreSQL and Redis.", "salary": "18-35 Lacs", "skills": ["Python", "FastAPI", "PostgreSQL", "Redis"]},
            {"title": "Frontend Engineer", "description": "CSS, JavaScript and Tailwind.", "salary": "12-25 Lacs", "skills": ["JavaScript", "CSS", "Tailwind", "React"]}
        ]
    }
    
    selected_role = templates.get(role, templates["Software Developer"])
    
    jobs = []
    for item in selected_role:
        jobs.append({
            "title": item["title"],
            "description": item["description"],
            "salary": item["salary"],
            "role": role,
            "location": location,
            "skills": item["skills"]
        })
    return jobs

def inject():
    import sqlite3
    db_path = os.path.join("data", "jobs.db")
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            salary TEXT,
            role TEXT,
            location TEXT,
            extracted_skills TEXT,
            scraped_on DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    all_roles = ["Data Analyst", "Data Scientist", "ML Engineer", "Business Analyst", "Software Developer"]
    for role in all_roles:
        jobs = get_demo_jobs(role, "Bangalore")
        for job in jobs:
            cursor.execute('''
                INSERT INTO jobs (title, description, salary, role, location, extracted_skills)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (job["title"], job["description"], job["salary"], job["role"], job["location"], json.dumps(job["skills"])))
        
    conn.commit()
    conn.close()
    print("Zero-API demo data injected successfully!")

if __name__ == "__main__":
    inject()
