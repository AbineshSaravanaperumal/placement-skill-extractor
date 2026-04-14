# Job Scraper Module - Simplified for Demo Data Fallback
import os
import sqlite3
from datetime import date
from inject_demo_data import get_demo_jobs

print("SCRAPER_MODULE: Loaded version 1.0.7 - Permanent Demo Data Mode")

def get_db_path():
    """Returns absolute path to data/jobs.db using __file__."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return os.path.join(data_dir, "jobs.db")

def create_table():
    """Creates jobs table if it does not exist."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                salary TEXT,
                role TEXT,
                location TEXT,
                extracted_skills TEXT,
                scraped_on DATE DEFAULT (DATE('now'))
            )
        ''')
        conn.commit()
    finally:
        conn.close()

def scrape_jobs(role="Data Analyst", location="Bangalore", pages=3):
    """
    Returns job data for the given role.
    Uses rich demo data — no API key required.
    """
    print(f"Loading job data for: {role} in {location}")
    jobs = get_demo_jobs(role, location)
    print(f"Loaded {len(jobs)} jobs.")
    return jobs

def save_to_db(jobs):
    """Saves job listings to the database, skipping duplicates."""
    if not jobs:
        return 0
        
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    saved_count = 0
    skipped_count = 0
    current_date = date.today().isoformat()
    
    try:
        for i, job in enumerate(jobs):
            cursor.execute(
                "SELECT id FROM jobs WHERE title = ? AND scraped_on = ?", 
                (job["title"], current_date)
            )
            if cursor.fetchone():
                skipped_count += 1
            else:
                cursor.execute('''
                    INSERT INTO jobs (title, description, salary, role, location)
                    VALUES (?, ?, ?, ?, ?)
                ''', (job["title"], job["description"], job["salary"], job["role"], job["location"]))
                saved_count += 1
                
        conn.commit()
        print(f"Saved {saved_count} new jobs — skipped {skipped_count} duplicates")
    finally:
        conn.close()
    
    return saved_count

# Kept for compatibility with app.py imports if needed, but redirects to unified scrape_jobs
def scrape_naukri(role, location, pages=2):
    return scrape_jobs(role, location)

def scrape_timesjobs(role, location):
    return scrape_jobs(role, location)

if __name__ == "__main__":
    create_table()
    jobs = scrape_jobs()
    save_to_db(jobs)
