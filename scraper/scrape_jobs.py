# Job Scraper Module - Updated with TimesJobs Support
import os
import sqlite3
import requests
from bs4 import BeautifulSoup
import time
from datetime import date
import re

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

def scrape_naukri(role, location, pages=3):
    """Scrapes job listings from Naukri.com using requests and BeautifulSoup."""
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    # Naukri URL patterns
    role_slug = role.lower().replace(" ", "-")
    loc_slug = location.lower().replace(" ", "-")
    
    for page in range(pages):
        if page == 0:
            url = f"https://www.naukri.com/{role_slug}-jobs-in-{loc_slug}"
        else:
            url = f"https://www.naukri.com/{role_slug}-jobs-in-{loc_slug}-{page + 1}"
            
        print(f"Scraping page {page + 1} — {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Refined selectors for modern Naukri structure (uses article tags often)
            cards = soup.find_all(['div', 'article'], class_=re.compile(r'jobTuple|srp-jobtuple|cust-job-tuple|tuple', re.I))
            
            # Fallback for even more generic structure
            if not cards:
                cards = soup.select('article, .jobTuple, [class*="jobTuple"], [class*="JobTuple"]')
            
            print(f"Found {len(cards)} cards on page {page + 1}")
            
            for card in cards:
                try:
                    # Generic searches for title, desc and salary
                    title_tag = card.find(['a', 'div', 'h3'], class_=re.compile(r'title|job-title', re.I))
                    desc_tag = card.find(['span', 'div', 'p'], class_=re.compile(r'job-desc|description', re.I))
                    salary_tag = card.find(['span', 'li', 'i'], class_=re.compile(r'salary', re.I))
                    
                    title = title_tag.get_text(strip=True) if title_tag else "N/A"
                    description = desc_tag.get_text(strip=True) if desc_tag else "N/A"
                    salary = salary_tag.get_text(strip=True) if salary_tag else "Not disclosed"
                    
                    jobs.append({
                        "title": title,
                        "description": description,
                        "salary": salary,
                        "role": role,
                        "location": location
                    })
                except Exception as e:
                    continue
                    
            time.sleep(2)  # Delay between pages
            
        except Exception as e:
            print(f"Error scraping page {page + 1}: {e}")
            
    return jobs

def scrape_timesjobs(role, location):
    """Scrapes jobs from TimesJobs.com - much more friendly to requests."""
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # URL formatting
    role_q = role.replace(" ", "+")
    loc_q = location.replace(" ", "+")
    url = f"https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords={role_q}&txtLocation={loc_q}"
    
    print(f"Scraping TimesJobs — {url}")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        cards = soup.find_all('li', class_='clearfix job-bx wht-shd-bx')
        
        print(f"Found {len(cards)} live cards on TimesJobs")
        
        for card in cards:
            title = card.find('h2').text.strip()
            
            # TimesJobs has 'Key Skills' in a specific div
            key_skills_tag = card.find('span', string=re.compile(r'KeySkills', re.I))
            if key_skills_tag and key_skills_tag.find_next_sibling('span'):
                desc = key_skills_tag.find_next_sibling('span').text.strip()
            else:
                # Fallback to the general snippet
                desc = card.find('ul', class_='list-job-dtl clearfix').text.strip()
            
            salary_tag = card.find('i', class_='rupee')
            salary = salary_tag.parent.text.strip() if salary_tag else "Not disclosed"
            
            jobs.append({
                "title": title,
                "description": desc,
                "salary": salary,
                "role": role,
                "location": location
            })
    except Exception as e:
        print(f"TimesJobs error: {e}")
        
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
            
            if len(jobs) > 5 and (i + 1) % 5 == 0:
                print(f"Processed {i + 1}/{len(jobs)}...")
                
        conn.commit()
        print(f"Saved {saved_count} new jobs — skipped {skipped_count} duplicates")
    finally:
        conn.close()
    
    return saved_count

if __name__ == "__main__":
    create_table()
    # Try Naukri
    jobs = scrape_naukri("data-analyst", "bangalore", pages=2)
    # Fallback/Additional from TimesJobs
    jobs += scrape_timesjobs("data-analyst", "bangalore")
    
    save_to_db(jobs)
