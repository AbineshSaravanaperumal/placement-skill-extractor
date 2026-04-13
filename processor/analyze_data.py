import os
import sqlite3
import pandas as pd
from collections import Counter
import re

# module level merge rules
MERGE_RULES = {
    "nodejs": "node.js", "node js": "node.js",
    "ml": "machine learning",
    "js": "javascript",
    "powerbi": "power bi", "power-bi": "power bi",
    "my sql": "mysql",
    "mongo db": "mongodb", "mongo": "mongodb",
    "tensor flow": "tensorflow",
    "sklearn": "scikit-learn", "scikit learn": "scikit-learn",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "natural language processing": "nlp",
    "reactjs": "react", "react js": "react",
    "vuejs": "vue", "vue js": "vue",
    "github": "git",
    "ms excel": "excel", "microsoft excel": "excel",
    "ms sql": "sql server", "microsoft sql": "sql server",
}

def get_db_path():
    """Returns absolute path to data/jobs.db using __file__."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "data", "jobs.db")

def get_top_skills(all_skills, top_n=15):
    """Normalizes and counts professional skills from a list."""
    if not all_skills:
        return pd.DataFrame(columns=["Skill", "Count", "Percentage"])
    
    normalized = []
    for s in all_skills:
        s = s.lower().strip()
        # Apply merge rules
        s = MERGE_RULES.get(s, s)
        normalized.append(s)
        
    counts = Counter(normalized)
    total = len(normalized)
    
    data = []
    for skill, count in counts.most_common(top_n):
        percentage = round((count / total) * 100, 1)
        data.append({
            "Skill": skill.title(),
            "Count": count,
            "Percentage": percentage
        })
        
    return pd.DataFrame(data)

def extract_salary_data():
    """Parses numeric salary data from the database strings into LPA."""
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT salary FROM jobs WHERE salary IS NOT NULL AND salary != 'Not disclosed'"
        df = pd.read_sql_query(query, conn)
        conn.close()
    except:
        return None
        
    if df.empty:
        return None
        
    salaries = []
    for raw in df['salary']:
        try:
            # Handle formats like "3-6 Lacs", "₹4,00,000 - ₹8,00,000", "10 LPA"
            clean = raw.replace('₹', '').replace(',', '').lower()
            nums = re.findall(r'\d+\.?\d*', clean)
            
            if not nums:
                continue
                
            vals = [float(n) for n in nums]
            # Convert to LPA if value is absolute (e.g. 400000 -> 4.0)
            vals = [v/100000 if v > 1000 else v for v in vals]
            
            if len(vals) >= 2:
                min_s, max_s = vals[0], vals[1]
            else:
                min_s = max_s = vals[0]
                
            # Keep reasonable ranges (1 to 100 LPA)
            if 1 <= min_s <= 100 and 1 <= max_s <= 100 and min_s <= max_s:
                salaries.append({"min": min_s, "max": max_s, "avg": (min_s + max_s)/2})
        except:
            continue
            
    if len(salaries) < 3:
        return None
        
    return pd.DataFrame(salaries)

def get_skill_gap(top_skills_df, user_skills_list):
    """Compares user skills against top industry skills and returns gap insights."""
    if top_skills_df.empty:
        return {"already_have": [], "must_learn": [], "nice_to_have": [], "match_score": "0/0 (0%)"}

    user_skills = [s.lower().strip() for s in user_skills_list]
    top_skills = top_skills_df["Skill"].tolist()
    
    already_have = []
    missing = []
    
    for skill in top_skills:
        skill_lower = skill.lower()
        # Match if user skill exactly matches or is contained in the string
        if any(us == skill_lower or us in skill_lower for us in user_skills):
            already_have.append(skill)
        else:
            missing.append(skill)
            
    match_count = len(already_have)
    total_count = len(top_skills)
    percent = round((match_count / total_count) * 100, 1) if total_count > 0 else 0
    
    return {
        "already_have": already_have,
        "must_learn": missing[:5],
        "nice_to_have": missing[5:],
        "match_score": f"{match_count}/{total_count} ({percent}%)"
    }

if __name__ == "__main__":
    # Test block
    from extract_skills import process_all_jobs
    all_skills = process_all_jobs()
    top_df = get_top_skills(all_skills)
    print("\nTop Skills Table:")
    print(top_df)
