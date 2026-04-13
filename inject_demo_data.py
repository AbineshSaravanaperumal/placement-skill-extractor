import json
import os

def get_demo_jobs(role, location):
    """Returns a list of realistic demo jobs for a specific role and location."""
    
    # Generic templates to mix and match
    templates = {
        "Data Analyst": [
            {"title": "Senior Data Analyst", "description": "Looking for expert in Python, SQL and Tableau with experience in AWS.", "salary": "12-18 Lacs"},
            {"title": "Junior Analyst", "description": "Entry level role requiring SQL, Power BI and Excel.", "salary": "6-10 Lacs"},
            {"title": "BI Developer", "description": "Mastery in Power BI, SQL, and Snowflake.", "salary": "10-15 Lacs"}
        ],
        "Data Scientist": [
            {"title": "Staff Data Scientist", "description": "Need Machine Learning, TensorFlow, and Python skills for predictive modeling.", "salary": "25-45 Lacs"},
            {"title": "AI Researcher", "description": "Expertise in PyTorch, NLP, and Deep Learning required.", "salary": "30-50 Lacs"},
            {"title": "Machine Learning Associate", "description": "Focus on Scikit-Learn, Pandas and data cleaning.", "salary": "12-20 Lacs"}
        ],
        "ML Engineer": [
            {"title": "MLOps Engineer", "description": "Focus on Kubernetes, Docker, and Model Deployment via FastAPI.", "salary": "20-35 Lacs"},
            {"title": "Machine Learning Engineer", "description": "Strong skills in Spark, TensorFlow and Big Data processing.", "salary": "18-30 Lacs"},
            {"title": "Computer Vision Engineer", "description": "Experience with OpenCV, PyTorch and image processing.", "salary": "22-40 Lacs"}
        ],
        "Business Analyst": [
            {"title": "Product Business Analyst", "description": "Work with Stakeholders, Jira, and SQL to define product roadmaps.", "salary": "10-18 Lacs"},
            {"title": "Sr. Business Analyst", "description": "Proficiency in Advanced Excel, Tableau and Agile methodologies.", "salary": "15-25 Lacs"},
            {"title": "Market Data Analyst", "description": "Analyze market trends using SQL, R and Power BI.", "salary": "12-20 Lacs"}
        ],
        "Software Developer": [
            {"title": "Full Stack Developer (Next.js)", "description": "Strong React, Node.js and TypeScript skills for modern web apps.", "salary": "15-30 Lacs"},
            {"title": "Backend Software Engineer", "description": "Focus on Python FastAPI, PostgreSQL and Redis.", "salary": "18-35 Lacs"},
            {"title": "Frontend Engineer", "description": "Mastery of CSS, JavaScript and Tailwind required.", "salary": "12-25 Lacs"}
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
            "location": location
        })
    return jobs

def inject():
    import sqlite3
    db_path = os.path.join("data", "jobs.db")
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table just in case
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
                INSERT INTO jobs (title, description, salary, role, location)
                VALUES (?, ?, ?, ?, ?)
            ''', (job["title"], job["description"], job["salary"], job["role"], job["location"]))
        
    conn.commit()
    conn.close()
    print("Market-consistent demo data injected successfully!")

if __name__ == "__main__":
    inject()
