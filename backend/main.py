from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import sqlite3
import datetime
import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# --- Load .env from root project directory ---
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=dotenv_path)

# --- Database Path Setup ---
DB_PATH = BASE_DIR / "db" / "org_analysis.db"
os.makedirs(BASE_DIR / "db", exist_ok=True)

app = FastAPI()

# --- Database Setup ---
def init_db():
    # Convert Path object to string for SQLite compatibility
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_name TEXT,
        industry TEXT,
        challenge TEXT,
        situation TEXT,
        external_change TEXT,
        sources TEXT,
        strategic_issues TEXT,
        opportunities TEXT,
        priorities TEXT,
        initiatives TEXT,
        outcomes TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Input Schema ---
class OrgInput(BaseModel):
    org_name: str
    industry: str
    challenge: str

# --- External Research Helper ---
def fetch_industry_trends(industry: str):
    api_key = os.getenv("TAVILY_API_KEY")
    
    if api_key:
        print(f"DEBUG: TAVILY_API_KEY detected -> {api_key[:8]}...")
    else:
        print("DEBUG: Missing TAVILY_API_KEY in environment variables.")
        return f"Fallback evidence: {industry} industry facing disruption.", []

    url = "https://api.tavily.com/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "api_key": api_key,
        "query": f"{industry} industry transformation trends 2026",
        "max_results": 3
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=8)
        print("DEBUG: Tavily status code =", response.status_code)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            snippets = [
                {
                    "title": item.get("title", "Article"),
                    "url": item.get("url", "")
                }
                for item in results
            ]
            
            if snippets:
                external_change = "\n".join([f"- {s['title']}: {s['url']}" for s in snippets])
                return external_change, snippets
            else:
                print("DEBUG: Tavily returned empty results list.")
        else:
            print("DEBUG: Tavily error response =", response.text)
            
    except Exception as e:
        print("DEBUG: fetch_industry_trends exception =", e)

    return f"Fallback evidence: {industry} industry facing disruption.", []

# --- Analysis Logic ---
def analyze_org(org_name: str, industry: str, challenge: str):
    situation = f"{org_name} operates in {industry} and faces {challenge}."
    external_change, sources = fetch_industry_trends(industry)

    ind = industry.strip().lower()
    if "retail" in ind:
        strategic_issues = f"{org_name} must adapt to e-commerce competition and supply chain challenges."
        opportunities = "Expand online presence, use AI for personalized shopping, and improve logistics."
        priorities = "Focus first on digital transformation and customer engagement."
        initiatives = "Upgrade e-commerce platforms, adopt AI recommendation engines, optimize delivery networks."
        outcomes = "Higher sales, better customer loyalty, stronger competitiveness."
    elif "education" in ind:
        strategic_issues = f"{org_name} must embrace digital learning and address accessibility gaps."
        opportunities = "Adopt online platforms, AI tutoring, and blended learning models."
        priorities = "Focus first on digital curriculum and teacher training."
        initiatives = "Develop e-learning modules, train staff in digital tools, expand remote learning access."
        outcomes = "Improved student outcomes, wider reach, modernized teaching methods."
    elif "bank" in ind or "finance" in ind:
        strategic_issues = f"{org_name} must modernize legacy systems and compete with fintechs."
        opportunities = "Adopt digital lending, AI fraud detection, and mobile-first banking."
        priorities = "Focus first on core banking modernization."
        initiatives = "Upgrade loan systems, deploy AI risk models, expand mobile apps."
        outcomes = "Faster approvals, lower costs, improved customer retention."
    else:
        strategic_issues = f"{org_name} must address inefficiencies and adapt to new technologies."
        opportunities = "Adopt AI-driven automation, enhance customer experience, and optimize operations."
        priorities = "Focus first on AI adoption in core processes."
        initiatives = "Launch pilot AI projects, train staff, modernize IT infrastructure."
        outcomes = "Improved efficiency, reduced costs, stronger market position."

    results = {
        "situation": situation,
        "external_change": external_change,
        "sources": sources if isinstance(sources, list) else [],
        "strategic_issues": strategic_issues,
        "opportunities": opportunities,
        "priorities": priorities,
        "initiatives": initiatives,
        "outcomes": outcomes
    }
    return results

# --- Analyze Endpoint ---
@app.post("/analyze")
def analyze(input_data: OrgInput):
    results = analyze_org(input_data.org_name, input_data.industry, input_data.challenge)

    # Convert Path object to string for SQLite compatibility
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO analysis (
        org_name, industry, challenge,
        situation, external_change, sources, strategic_issues,
        opportunities, priorities, initiatives, outcomes, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        input_data.org_name, input_data.industry, input_data.challenge,
        results["situation"], results["external_change"],
        json.dumps(results["sources"]),
        results["strategic_issues"], results["opportunities"], results["priorities"],
        results["initiatives"], results["outcomes"], datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

    org_dict = input_data.model_dump() if hasattr(input_data, "model_dump") else input_data.dict()
    return {"organization": org_dict, "analysis": results}

# --- File Upload Endpoint ---
@app.post("/upload")
async def upload_org_file(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    return {"filename": file.filename, "extracted_text": text[:500]}