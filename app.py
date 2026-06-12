import os
import sys
import io
import json
import re
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import contextmanager

# Import agents
from agents.agent1 import startup_discovery_agent
from agents.market_research_agent import market_research_agent
from agents.mvp_planner_agent import mvp_planner_agent
from agents.pitch_deck_agent import pitch_deck_agent
import services.gemini as gemini_service
from services.vector_store import retrieve_startups

app = FastAPI(title="StartupForge AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration State
class Config(BaseModel):
    groq_api_key: str = ""
    demo_mode: bool = True

CONFIG_STATE = {
    "groq_api_key": os.getenv("GROQ_API_KEY", ""),
    "demo_mode": True
}

# Context manager to capture stdout print statements
@contextmanager
def capture_stdout():
    old_out = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = old_out

@app.get("/api/config")
def get_config():
    return {
        "groq_api_key_set": bool(CONFIG_STATE["groq_api_key"]),
        "demo_mode": CONFIG_STATE["demo_mode"]
    }

@app.post("/api/config")
def update_config(config: Config):
    global CONFIG_STATE
    CONFIG_STATE["groq_api_key"] = config.groq_api_key
    CONFIG_STATE["demo_mode"] = config.demo_mode
    if config.groq_api_key:
        gemini_service.set_api_key(config.groq_api_key)
    return {"status": "success", "demo_mode": CONFIG_STATE["demo_mode"]}

# --- API Endpoints for Agents ---

class UserProfile(BaseModel):
    skills: str
    interests: str
    experience: str
    budget: str
    goal: str

@app.post("/api/agents/discovery")
def run_discovery(profile: UserProfile):
    profile_dict = profile.model_dump()
    logs = ""
    
    if CONFIG_STATE["demo_mode"]:
        # Mock Discovery Agent
        logs = "[1] Analyzing Intent...\n[2] Retrieving Startups...\n[3] Finding Patterns...\n[4] Finding Market Gaps...\n[5] Generating Opportunities...\n[6] Scoring Opportunities...\n[7] Generating Blueprint...\n"
        
        interest = profile.interests.lower()
        if "education" in interest or "learn" in interest or "school" in interest:
            name = "CurricuLabs AI"
            problem = "Teachers spend too much time creating personalized educational content, leading to burn-out and generic learning experiences for students."
            solution = "An AI-powered content generation assistant that generates lessons, custom quizzes, and worksheets aligned to national curricula instantly."
            target_users = "Teachers, Tutors, and Schools"
            rev = "SaaS Subscription: $15/month for teachers, enterprise school packages starting at $150/month."
            mvp = "1. AI Lesson Plan Builder\n2. Interactive Quiz Generator\n3. Export to PDF/Google Drive"
            opps = "CurricuLabs AI, EdBot Personal Tutor, QuickGrading AI"
        elif "finance" in interest or "money" in interest or "wealth" in interest:
            name = "WealthForge AI"
            problem = "Young professionals struggle with basic wealth management and find professional advisors too expensive."
            solution = "An automated AI agent that tracks cashflow, optimizes tax strategies, and executes micro-investing automatically based on personalized goals."
            target_users = "Gen Z and Millennials"
            rev = "Premium Subscription: $8/month + 0.1% managed asset fee."
            mvp = "1. Automated Expense Tracker\n2. AI Financial Health Dashboard\n3. Smart Micro-Savings Vault"
            opps = "WealthForge AI, BudgetBot, TaxOptimizer AI"
        else:
            name = "TaskForge AI"
            problem = "Small businesses struggle to manage repetitive tasks, emails, and customer replies, limiting their growth potential."
            solution = "A no-code workspace that allows non-technical business managers to spin up AI agents that automatically resolve emails and draft reports."
            target_users = "Small & Medium Businesses"
            rev = "Usage-based tiers starting at $29/month."
            mvp = "1. Email inbox integration\n2. Simple automation script designer\n3. PDF/CSV reporting dashboard"
            opps = "TaskForge AI, AgentInbox, AutoReport AI"

        blueprint_dict = {
            "startup_name": name,
            "problem_statement": problem,
            "solution": solution,
            "target_users": target_users,
            "revenue_model": rev,
            "competitive_advantage": "Easy customization, native tool integration, low-cost API efficiency.",
            "why_now": "Rapid capability scaling in LLMs makes structured task workflows highly accurate.",
            "mvp_features": mvp,
            "go_to_market_strategy": "Micro-influencer marketing, content marketing for search intent, and directory submissions."
        }
        
        blueprint_str = f"```json\n{json.dumps(blueprint_dict, indent=4)}\n```"
        result = {
            "intent": "Extracting domain interests...",
            "retrieved_startups": [
                "\nStartup Name:\nAdaptaLearn\n\nOne Liner:\nAI powered adaptive learning platform.\n",
                "\nStartup Name:\nOptimizely\n\nOne Liner:\nThe first all-in-one operating system for marketing\n"
            ],
            "patterns": "Increasing focus on hyper-personalization, subscription SaaS business models, and low cost of operation.",
            "market_gaps": "Lack of custom tools for non-technical creators to customize lessons/workbooks.",
            "opportunities": opps,
            "scores": "Innovaton: 85%, Market Potential: 90%, Feasibility: 95%",
            "blueprint": blueprint_str
        }
    else:
        # Live Mode
        if not CONFIG_STATE["groq_api_key"]:
            raise HTTPException(status_code=400, detail="Groq API Key is not set.")
            
        with capture_stdout() as buffer:
            try:
                result = startup_discovery_agent(profile_dict)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Discovery agent execution failed: {str(e)}")
        logs = buffer.getvalue()
        
    return {
        "status": "success",
        "logs": logs,
        "result": result
    }

class ResearchInput(BaseModel):
    startup_name: str
    problem: str
    solution: str
    target_users: str

@app.post("/api/agents/research")
def run_research(startup: ResearchInput):
    logs = ""
    
    if CONFIG_STATE["demo_mode"]:
        logs = "Searching StackOverflow...\nSearching HackerNews...\nRetrieving YC Startups...\nAnalyzing Competitors...\nFinding Pain Points...\nAnalyzing Demand...\nRanking Opportunities...\nValidating Opportunity...\nGetting Investor Feedback...\n"
        
        # Real-time search of YC startups locally via ChromaDB (doesn't require Groq API key)
        yc_competitors = []
        try:
            query = f"{startup.problem} {startup.solution}"
            yc_competitors = retrieve_startups(query, n_results=4)
        except Exception as e:
            print("ChromaDB query error (using fallback):", e)
            yc_competitors = ["Startup Name: EduBot\nIndustries: Education\nOne Liner: Automated tutoring helper.",
                              "Startup Name: LessonScribe\nIndustries: B2B, Education\nOne Liner: Lesson planning software."]
            
        competitors_analysis = {
            "direct_competitors": ["ClassCraft AI", "EducationCopilot"],
            "indirect_competitors": ["ChatGPT", "Quizlet", "Google Classroom"],
            "competitor_strengths": "Established user base, existing templates, integrations.",
            "competitor_weaknesses": "Generic prompts, high monthly costs, complex setup for teachers.",
            "differentiation_opportunities": "Deep integration with school curricula standard formats, offline worksheet generator.",
            "founder_advantages": "Low cost of development, direct feedback from student community."
        }
        
        pain_points = {
            "common_complaints": [
                "Templates are too generic and don't match specific textbooks",
                "Grading tools take too long to configure",
                "Pricing is too high for individual educators"
            ],
            "missing_features": ["Curriculum standards alignment", "Easy parents-sharing portal"]
        }
        
        demand = {
            "market_demand_score": 88,
            "growth_signals": "High search volume on keywords like 'AI lesson planner' and 'AI quiz builder'.",
            "adoption_potential": "Excellent. Teachers are actively seeking ways to cut down administrative planning hours."
        }
        
        ranked = [
            {"rank": 1, "opportunity_name": f"{startup.startup_name} Core Planner", "problem": startup.problem, "score": 92},
            {"rank": 2, "opportunity_name": "AI Auto-Grader Add-on", "problem": "Grading essays is slow.", "score": 85},
            {"rank": 3, "opportunity_name": "Curriculum Exporter", "problem": "Exporting plans to PDF/MS Word is messy.", "score": 80}
        ]
        
        validation = {
            "market_demand_score": 88,
            "competition_score": 65,
            "founder_market_fit_score": 90,
            "buildability_score": 95,
            "scalability_score": 80,
            "execution_risk_score": 35,
            "opportunity_score": 85,
            "can_founder_build": "Yes, with Python and React.",
            "time_to_mvp": "2-3 weeks",
            "mvp_cost_estimate": "$200 for initial APIs/Hosting",
            "early_adopters": "Individual school teachers, freelance tutors, home-schooling parents",
            "beachhead_market": "High School STEM Teachers"
        }
        
        investor = {
            "founder_market_fit_analysis": "Highly aligned. Being a student provides direct insight into classroom mechanics.",
            "fundability_score": 78,
            "investment_recommendation": "YES (Pre-Seed/YC Batch). Low cost of operations and fast build time make this highly capital efficient.",
            "strengths": ["Clear high-utility pain point", "Fast MVP potential", "Low initial infrastructure costs"],
            "weaknesses": ["Low switching costs for competitors", "K-12 budget sales cycles can be slow"],
            "risks": ["Fast copycats from larger EdTech platforms"]
        }
        
        result = {
            "startup_context": startup.model_dump(),
            "yc_startups": yc_competitors,
            "competitors": json.dumps(competitors_analysis, indent=4),
            "pain_points": json.dumps(pain_points, indent=4),
            "demand": json.dumps(demand, indent=4),
            "ranked_opportunities": json.dumps(ranked, indent=4),
            "validation": json.dumps(validation, indent=4),
            "investor_feedback": json.dumps(investor, indent=4)
        }
    else:
        # Live Mode
        if not CONFIG_STATE["groq_api_key"]:
            raise HTTPException(status_code=400, detail="Groq API Key is not set.")
            
        with capture_stdout() as buffer:
            try:
                result = market_research_agent(startup_idea=startup.model_dump())
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Market research agent execution failed: {str(e)}")
        logs = buffer.getvalue()
        
    return {
        "status": "success",
        "logs": logs,
        "result": result
    }

class MVPPlannerInput(BaseModel):
    startup_idea: dict
    user_profile: dict

@app.post("/api/agents/mvp-planner")
def run_mvp_planner(data: MVPPlannerInput):
    logs = ""
    
    if CONFIG_STATE["demo_mode"]:
        logs = "Retrieving YC Startups...\nGenerating Features...\nDesigning Tech Stack...\nDesigning Database...\nGenerating APIs...\nDesigning UI...\nCreating Roadmap...\nEstimating Costs...\nAnalyzing Risks...\nFounder Fit...\nBuildability...\nInvestor Readiness...\nRevenue Strategy...\nLaunch Strategy...\nSuccess Probability...\n"
        
        features = {
            "mvp_features": [
                {"name": "Dynamic Lesson Plan Customizer", "description": "Form inputs to select subject, grade, duration, and generate HTML lessons."},
                {"name": "Instant Quiz Exporter", "description": "Generates multiple-choice questions with answer keys in markdown or PDF."},
                {"name": "Lesson Catalog Dashboard", "description": "Saves historical lessons inside PostgreSQL."}
            ],
            "premium_features": [
                {"name": "Automated Grading Assistant", "description": "Uses AI to evaluate text answers and suggest grades."},
                {"name": "Classroom Sharing Hub", "description": "Real-time portal to push material to students directly."}
            ],
            "differentiators": "Curriculum-aligned standards, extremely simple UX, direct PDF/print optimization."
        }
        
        tech_stack = {
            "frontend": "React with Tailwind CSS (Vite)",
            "backend": "Python, FastAPI",
            "database": "PostgreSQL (for profiles/history), ChromaDB (for course context embeddings)",
            "hosting": "Render.com / Supabase (Free tier)",
            "ai_integration": "Groq LLaMA 3.1 8B Instant (low cost, ultra-fast responses)"
        }
        
        db_schema = """CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    title VARCHAR(200),
    subject VARCHAR(100),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quizzes (
    id SERIAL PRIMARY KEY,
    lesson_id INT REFERENCES lessons(id),
    questions JSONB
);"""

        apis = [
            {"method": "POST", "route": "/api/auth/register", "description": "Registers new user"},
            {"method": "POST", "route": "/api/lessons/generate", "description": "Triggers LLM to generate custom lesson plan"},
            {"method": "GET", "route": "/api/lessons", "description": "Gets historical generated lessons"},
            {"method": "POST", "route": "/api/quizzes/generate", "description": "Generates custom quiz questions"}
        ]
        
        ui_layout = [
            {"screen": "Login / Register Dashboard", "components": "Simple auth, Google Single Sign-On"},
            {"screen": "Workplace Generator Console", "components": "Multi-field forms for Subject, Topic, Grade, Tone, and Generate button"},
            {"screen": "Plan Viewer & Editor Workspace", "components": "Frosted glass container showing generated text with inline edit and print buttons"},
            {"screen": "Quizzes Hub", "components": "List of generated quizzes with download actions"}
        ]
        
        roadmap = [
            {"week": "Week 1", "goal": "Setup database schemas and build core FastAPI authentication routes + static file hooks."},
            {"week": "Week 2", "goal": "Build frontend React layout. Connect generate endpoint API to Groq client."},
            {"week": "Week 3", "goal": "Integrate ChromaDB to enable context retrieval from textbook references. Add PDF downloader module."},
            {"week": "Week 4", "goal": "Execute final testing, launch free beta on Render.com, and deploy first 100 teacher outreach emails."}
        ]
        
        costs = {
            "development_cost": "$0 (built by founder)",
            "monthly_cost": "$7 (Render.com web hosting fee)",
            "ai_cost": "$0.02 per 100 requests (Groq API standard usage)",
            "hosting_cost": "$0 (Supabase free tier DB)"
        }
        
        risks = {
            "technical_risks": "API rate limits, server cold starts.",
            "product_risks": "Teachers finding prompt outputs too generic.",
            "market_risks": "Schools blocking AI-generated curriculum helpers."
        }
        
        success = {
            "success_probability": 85,
            "biggest_opportunity": "Tapping into high-stress school administration burnout.",
            "biggest_risk": "Lack of school board software approval channels.",
            "recommendation": "Go direct-to-teacher, build grass-roots adoption, avoid enterprise sales early."
        }
        
        result = {
            "yc_startups": ["Demo Gorilla", "Taiv"],
            "features": json.dumps(features, indent=4),
            "tech_stack": json.dumps(tech_stack, indent=4),
            "database": db_schema,
            "apis": json.dumps(apis, indent=4),
            "ui": json.dumps(ui_layout, indent=4),
            "roadmap": json.dumps(roadmap, indent=4),
            "costs": json.dumps(costs, indent=4),
            "risks": json.dumps(risks, indent=4),
            "founder_fit": "Founder Fit Score: 9/10",
            "buildability": "Buildability Score: 10/10 - Core features are highly feasible for a single Python/React developer.",
            "investor_readiness": "Investor Readiness Score: 8/10",
            "revenue_strategy": "Freemium SaaS ($15/month for unlimited exports)",
            "launch_strategy": "Launch on ProductHunt, email K-12 educators directly, share on Reddit subreddits",
            "success_probability": json.dumps(success, indent=4)
        }
    else:
        # Live Mode
        if not CONFIG_STATE["groq_api_key"]:
            raise HTTPException(status_code=400, detail="Groq API Key is not set.")
            
        with capture_stdout() as buffer:
            try:
                result = mvp_planner_agent(data.startup_idea, data.user_profile)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"MVP planner agent execution failed: {str(e)}")
        logs = buffer.getvalue()
        
    return {
        "status": "success",
        "logs": logs,
        "result": result
    }

class PitchDeckInput(BaseModel):
    startup_context: dict
    market_validation: str
    architect_report: dict

@app.post("/api/agents/pitch-deck")
def run_pitch_deck(data: PitchDeckInput):
    logs = ""
    
    if CONFIG_STATE["demo_mode"]:
        logs = "Running Pitch Deck Agent...\nProcessing market validation metrics...\nFormatting slides...\nGenerating pitch deck JSON...\n"
        
        slides = [
            {"slide_number": 1, "title": "Company Name & Vision", "bullets": [data.startup_context.get("startup_name", "AdaptaLearn"), "AI-powered custom learning pipelines for classrooms", "Empowering educators, saving hours daily"]},
            {"slide_number": 2, "title": "The Problem", "bullets": ["Teachers spend 10+ hours per week designing personalized materials", "Burnout leads to lower teacher retention rates", "Students suffer from generic learning packages"]},
            {"slide_number": 3, "title": "The Solution", "bullets": ["Instant AI generator tailored to local curriculum systems", "Generate lesson plans, quizzes, and files in 5 seconds", "Interactive, printer-friendly outputs ready out of the box"]},
            {"slide_number": 4, "title": "Market Opportunity", "bullets": ["70M+ teachers globally", "Total addressable EdTech creator market: $15B+", "Initial beachhead: High School Science & Math Teachers"]},
            {"slide_number": 5, "title": "Competitive Advantages", "bullets": ["LMS integrations (Canvas, Classroom)", "Curriculum standards mapping support", "Ultra-fast execution times via LLaMA models"]},
            {"slide_number": 6, "title": "Product Overview", "bullets": ["Simple forms input console", "Rich text interactive workspace editor", "Export and cataloging modules"]},
            {"slide_number": 7, "title": "Business Model", "bullets": ["Freemium plan: 3 free plan generations per month", "Pro tier: $15/month for unlimited exports & grading support", "School districts: $99/month/school contract package"]},
            {"slide_number": 8, "title": "Go-To-Market", "bullets": ["Direct cold email outreach to classroom educators", "Submissions to EdTech directories and Reddit communities", "Viral growth loops via student-facing quizzes"]},
            {"slide_number": 9, "title": "Roadmap", "bullets": ["Month 1: Develop MVP, core auth, and PDF exporter", "Month 2: Beta release, acquire first 100 classroom signups", "Month 3: Rollout grading assistant and school integrations"]},
            {"slide_number": 10, "title": "The Ask", "bullets": ["Seeking $150K Pre-Seed investment", "Funds used for server scale, database scaling, and local marketing", "Targeting 5,000 monthly active educators in 6 months"]}
        ]
        
        result = json.dumps(slides, indent=4)
    else:
        # Live Mode
        if not CONFIG_STATE["groq_api_key"]:
            raise HTTPException(status_code=400, detail="Groq API Key is not set.")
            
        with capture_stdout() as buffer:
            try:
                result = pitch_deck_agent(data.startup_context, data.market_validation, data.architect_report)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Pitch deck agent execution failed: {str(e)}")
        logs = buffer.getvalue()
        
    return {
        "status": "success",
        "logs": logs,
        "result": result
    }

# Query YC database
@app.get("/api/startups")
def get_startups(query: str = "AI"):
    try:
        docs = retrieve_startups(query, n_results=10)
        startups = []
        for doc in docs:
            # Parse simple info
            lines = doc.strip().split("\n")
            info = {}
            current_key = None
            for line in lines:
                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].strip().lower().replace(" ", "_")
                    val = parts[1].strip()
                    info[key] = val
                    current_key = key
                elif current_key and line.strip():
                    info[current_key] += " " + line.strip()
            startups.append(info)
        return {"status": "success", "results": startups}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# Serve static frontend dashboard
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/", StaticFiles(directory="static", html=True), name="static")
