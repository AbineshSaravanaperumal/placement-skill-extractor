import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import os
import sys
from datetime import datetime
from openai import OpenAI

# Add project root to sys.path
import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scraper.scrape_jobs import create_table, scrape_naukri, scrape_timesjobs, save_to_db, get_db_path
from processor.extract_skills import process_all_jobs, get_api_key
from processor.analyze_data import get_top_skills, extract_salary_data, get_skill_gap
import json

def seed_data():
    """Seeds the database with sample data if it's empty."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM jobs")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    sample_jobs = [
        ("Senior Data Analyst", "Python, SQL, Tableau, AWS, Excel", "12-18 Lacs", "Data Analyst", "Bangalore", ["Python", "SQL", "Tableau", "AWS", "Excel"]),
        ("Data Scientist", "Machine Learning, TensorFlow, Python, Statistics", "15-25 Lacs", "Data Scientist", "Bangalore", ["Python", "Machine Learning", "TensorFlow", "Statistics"]),
        ("Junior Analyst", "SQL, Power BI, Excel, Statistics", "6-10 Lacs", "Data Analyst", "Bangalore", ["SQL", "Power BI", "Excel"]),
        ("Data Engineer", "SQL, Spark, GCP, Python, Hadoop", "18-28 Lacs", "Data Analyst", "Bangalore", ["SQL", "Spark", "GCP", "Python"]),
        ("BI Developer", "Power BI, SQL, Snowflake, Tableau", "10-15 Lacs", "Data Analyst", "Bangalore", ["Power BI", "SQL", "Snowflake", "Excel"])
    ]
    
    for title, desc, sal, role, loc, skills in sample_jobs:
        cursor.execute('''
            INSERT INTO jobs (title, description, salary, role, location, extracted_skills)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, desc, sal, role, loc, json.dumps(skills)))
    
    conn.commit()
    conn.close()

# Page Config
st.set_page_config(
    page_title="SkillMap — Placement Prep",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp { background: #0a0f1e; color: #e8eaf0; }
    .stButton > button { 
        background: #00d4aa; color: #0a0f1e; font-weight: 700; border: none; border-radius: 8px; width: 100%;
    }
    .stButton > button:hover { background: #00b894; border: none; color: #0a0f1e; }
    div[data-testid="stMetricValue"] { font-size: 26px; font-weight: 700; color: #00d4aa; }
    .stDivider { border-bottom: 1px solid #1f2937; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🎯 SkillMap")
    st.caption("Placement Prep Skill Extractor")
    st.divider()
    
    role = st.selectbox("Select Role", ["Data Analyst", "Data Scientist", "ML Engineer", "Business Analyst", "Software Developer"])
    location = st.selectbox("Select Location", ["Bangalore", "Hyderabad", "Mumbai", "Chennai", "Remote"])
    top_n = st.slider("Number of skills to show", 5, 20, 15)
    
    st.divider()
    
    if st.button("🔄 Refresh Data"):
        with st.spinner("Initializing Database..."):
            create_table()
        
        with st.spinner(f"Scraping live jobs for {role}..."):
            # Aggregating from multiple sources
            jobs = scrape_naukri(role, location, pages=2)
            jobs += scrape_timesjobs(role, location)
            save_to_db(jobs)
            
        with st.spinner(f"Extracting skills for {len(jobs)} jobs via AI..."):
            process_all_jobs()
            
        st.success(f"Successfully processed {len(jobs)} live jobs!")
        st.rerun()

    st.divider()
    
    # Data Freshness
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(scraped_on), COUNT(*) FROM jobs")
        last_date, count = cursor.fetchone()
        conn.close()
        
        if last_date:
            st.caption(f"🟢 Updated: {last_date}")
            st.caption(f"📊 {count} jobs in DB")
        else:
            st.warning("🔴 No data — click Refresh")
    except:
        st.warning("🔴 Database not initialized")

# Main Area
st.title("🎯 Placement Prep Skill Extractor")
st.caption("Know exactly which skills are in demand before you apply.")

# Initialize DB Table and seed if empty
create_table()
seed_data()

# Check for data
db_path = get_db_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
try:
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE role = ?", (role,))
    job_count = cursor.fetchone()[0]
except:
    job_count = 0
finally:
    conn.close()

if job_count == 0:
    st.warning(f"No data found for {role} in {location}.")
    st.info("Please use the sidebar to 'Refresh Data' for this combination.")
    st.stop()

# Load Data
with st.spinner(f"Loading {role} data..."):
    all_skills = process_all_jobs(role_filter=role)
    skill_df = get_top_skills(all_skills, top_n)
    salary_df = extract_salary_data(role_filter=role)

if skill_df.empty:
    st.warning("No skills processed yet.")
    st.info("Click 'Refresh Data' in the sidebar to start extraction.")
    st.stop()

# 4 KPI Columns
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Jobs Analysed", job_count)
with kpi2:
    st.metric("Unique Skills Found", len(skill_df))
with kpi3:
    med_sal = "N/A"
    if salary_df is not None:
        med_sal = f"₹{round(salary_df['avg'].median(), 1)}L"
    st.metric("Median Salary", med_sal)
with kpi4:
    top_skill = skill_df.iloc[0]["Skill"] if not skill_df.empty else "—"
    st.metric("Top Skill", top_skill)

st.divider()

# Charts
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🔥 Top Requested Technical Skills")
    if not skill_df.empty:
        fig = px.bar(
            skill_df, 
            x="Percentage", 
            y="Skill", 
            orientation='h',
            color="Percentage",
            color_continuous_scale="Teal",
            text="Percentage"
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            xaxis_range=[0, 110],
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e8eaf0",
            coloraxis_showscale=False,
            height=max(420, len(skill_df) * 38),
            margin=dict(l=0, r=0, t=20, b=0)
        )
        st.plotly_chart(fig, theme="streamlit", width="stretch")
    else:
        st.info("Insufficient data for charting.")

with col_right:
    st.subheader("💰 Salary Range (LPA)")
    if salary_df is not None:
        fig = go.Figure()
        fig.add_trace(go.Box(y=salary_df['min'], name='Min Salary', marker_color='#00d4aa', boxpoints='outliers'))
        fig.add_trace(go.Box(y=salary_df['max'], name='Max Salary', marker_color='#3b82f6', boxpoints='outliers'))
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e8eaf0",
            height=380,
            yaxis_title="LPA",
            margin=dict(l=0, r=0, t=20, b=0)
        )
        st.plotly_chart(fig, theme="streamlit", width="stretch")
    else:
        st.info("Salary data not available for this set.")

st.divider()

# Full Table
st.subheader("📋 Full Skill Table")
search = st.text_input("Filter skills...", placeholder="Search (e.g. Python, SQL)")
filtered_df = skill_df[skill_df['Skill'].str.contains(search, case=False)] if search else skill_df

st.dataframe(
    filtered_df,
    column_config={
        "Percentage": st.column_config.ProgressColumn("Demand Score", format="%.1f%%", min_value=0, max_value=100)
    },
    hide_index=True,
    width="stretch"
)

today_str = datetime.now().strftime("%Y%m%d")
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    "📥 Download CSV",
    csv,
    f"skills_{role.lower().replace(' ', '_')}_{location.lower()}_{today_str}.csv",
    "text/csv"
)

st.divider()

# Skill Gap
st.subheader("🎯 Your Skill Gap")
user_input = st.text_input("Enter your current skills (comma separated)", placeholder="Python, SQL, Excel")

if user_input:
    user_skills = [s.strip() for s in user_input.split(",") if s.strip()]
    gap = get_skill_gap(skill_df, user_skills)
    
    g1, g2, g3 = st.columns(3)
    with g1:
        st.success(f"✅ Already have\n\n" + " · ".join(gap["already_have"]))
    with g2:
        st.error(f"🔴 Must learn next\n\n" + " · ".join(gap["must_learn"]))
    with g3:
        st.warning(f"🟡 Nice to have\n\n" + " · ".join(gap["nice_to_have"][:4]))
        
    # Parse progress
    try:
        score_val = float(gap["match_score"].split("(")[1].split("%")[0]) / 100
        st.markdown(f"**Match Score: {gap['match_score']}**")
        st.progress(score_val)
    except:
        pass
        
    if st.button("📅 Generate 30-Day Study Plan"):
        with st.spinner("AI is crafting your personal learning roadmap..."):
            try:
                client = OpenAI(api_key=get_api_key())
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a career coach. Create a structured 30-day learning plan based on required skills."},
                        {"role": "user", "content": f"I want to become a {role}. I already know: {', '.join(gap['already_have'])}. I need to learn: {', '.join(gap['must_learn'])}. Give me a week-by-week study plan to master these basics."}
                    ]
                )
                st.text_area("Your 30-Day Plan", value=response.choices[0].message.content, height=300)
            except Exception as e:
                st.error(f"AI Error: {e}")

st.divider()
st.caption(f"Last updated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Total {job_count} listings analyzed | Built by Abinesh")
