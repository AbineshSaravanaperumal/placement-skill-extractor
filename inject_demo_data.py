import sqlite3
import json
import os

def inject():
    db_path = os.path.join("data", "jobs.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Sample jobs with skills
    demo_jobs = [
        ("Senior Data Analyst", "Looking for expert in Python, SQL and Tableau with experience in AWS.", "12-18 Lacs", "Data Analyst", "Bangalore", ["Python", "SQL", "Tableau", "AWS", "Excel"]),
        ("Data Scientist", "Need Machine Learning, TensorFlow, and Python skills.", "15-25 Lacs", "Data Analyst", "Bangalore", ["Python", "Machine Learning", "TensorFlow", "Statistics"]),
        ("Junior Analyst", "Entry level role requiring SQL, Power BI and Excel.", "6-10 Lacs", "Data Analyst", "Bangalore", ["SQL", "Power BI", "Excel"]),
        ("Data Engineer", "Focus on SQL, Spark, and GCP.", "20-30 Lacs", "Data Analyst", "Bangalore", ["SQL", "Spark", "GCP", "Python"]),
        ("BI Developer", "Mastery in Power BI, SQL, and Snowflake.", "10-15 Lacs", "Data Analyst", "Bangalore", ["Power BI", "SQL", "Snowflake", "Excel"])
    ]
    
    for title, desc, sal, role, loc, skills in demo_jobs:
        cursor.execute('''
            INSERT INTO jobs (title, description, salary, role, location, extracted_skills)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, desc, sal, role, loc, json.dumps(skills)))
        
    conn.commit()
    conn.close()
    print("Demo data injected successfully!")

if __name__ == "__main__":
    inject()
