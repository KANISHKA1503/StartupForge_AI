import json
from services.gemini import generate, generate_json
from services.vector_store import retrieve_startups


def retrieve_yc_context(startup_context):
    query = f"""
    {startup_context.get('problem_statement') or startup_context.get('problem', '')}
    {startup_context.get('solution', '')}
    {startup_context.get('target_users', '')}
    """
    return retrieve_startups(query=query, n_results=5)


# ==========================================
# FIX 2: BATCHED PROMPTS (14 calls -> 4 calls)
# ==========================================

def batch_product_spec(startup_context, yc_docs):
    """
    BATCH 1 of 4: Combines Features + Tech Stack + DB Schema + REST APIs into a single LLM call.
    Reduces token overhead from 4 separate prompt headers/contexts to 1.
    """
    docs_text = "\n\n".join([doc for doc in yc_docs if isinstance(doc, str)])[:2000]

    prompt = f"""
You are a full-stack startup architect. Given the startup below, produce a complete product specification.

Startup:
{json.dumps(startup_context, indent=2)}

Similar YC Startups (for reference):
{docs_text}

Tech Stack Preferences: Python, FastAPI, PostgreSQL, ChromaDB.
Optimize for: solo founder, low budget, fast MVP, high scalability.
Avoid enterprise tools, expensive services, and NodeJS unless necessary.

Return a single JSON object with EXACTLY these top-level keys:

"features": {{
  "mvp_features": [list of strings],
  "premium_features": [list of strings],
  "differentiators": [list of strings],
  "competitive_advantages": [list of strings]
}}

"tech_stack": {{
  "frontend": string,
  "backend": string,
  "database": string,
  "vector_db": string,
  "ai_models": string,
  "architecture_notes": string
}}

"database": {{
  "tables": [
    {{
      "table_name": string,
      "columns": [list of strings],
      "relationships": string
    }}
  ]
}}

"apis": {{
  "endpoints": [
    {{
      "method": string,
      "path": string,
      "description": string,
      "request_body": object,
      "response": object
    }}
  ]
}}

Return ONLY valid JSON. Do NOT include markdown fences.
"""
    result = generate_json(prompt, expected_type=dict, temperature=0.4)

    features = result.get("features", {})
    tech_stack = result.get("tech_stack", {})
    database = result.get("database", {})
    if isinstance(database, dict):
        database = database.get("tables", [])
    apis = result.get("apis", {})
    if isinstance(apis, dict):
        apis = apis.get("endpoints", [])

    return features, tech_stack, database, apis


def batch_execution_plan(startup_context, features):
    """
    BATCH 2 of 4: Combines UI Design + 4-Week Roadmap + Cost Estimate into a single LLM call.
    All costs are in Indian Rupees (INR) — realistic for an Indian solo bootstrapped founder.
    """
    prompt = f"""
You are a senior product manager and startup financial advisor based in India.

Startup:
{json.dumps(startup_context, indent=2)}

MVP Features:
{json.dumps(features, indent=2)}

IMPORTANT: All cost values MUST be in Indian Rupees (INR ₹). Use realistic Indian market rates.
Typical Indian market rates for reference:
- Freelance developer: ₹500-₹2000/hour
- VPS Hosting (DigitalOcean/Railway): ₹800-₹3000/month
- Groq/OpenAI API: ₹2000-₹8000/month for moderate usage
- Domain + misc: ₹500-₹1500/month

Return a single JSON object with EXACTLY these top-level keys:

"ui": {{
  "pages": [
    {{
      "page_name": string,
      "components": [list of strings],
      "user_flow": string
    }}
  ]
}}

"roadmap": {{
  "weeks": [
    {{
      "week": integer (1 to 4),
      "goals": [list of strings],
      "deliverables": [list of strings]
    }}
  ]
}}

"costs": {{
  "currency": "INR",
  "development_cost_inr": integer (upfront one-time dev cost in ₹),
  "monthly_hosting_cost_inr": integer (server/hosting in ₹/month),
  "monthly_ai_cost_inr": integer (AI API calls in ₹/month),
  "monthly_misc_cost_inr": integer (domain, tools, services in ₹/month),
  "total_monthly_cost_inr": integer (sum of all monthly costs in ₹),
  "cost_breakdown": object (key-value pairs with ₹ amounts and descriptions),
  "notes": string (any important cost assumptions)
}}

Return ONLY valid JSON. Do NOT include markdown fences.
"""
    result = generate_json(prompt, expected_type=dict, temperature=0.4)

    ui = result.get("ui", {})
    if isinstance(ui, dict):
        ui = ui.get("pages", [])
    roadmap = result.get("roadmap", {})
    if isinstance(roadmap, dict):
        roadmap = roadmap.get("weeks", [])
    costs = result.get("costs", {})

    return ui, roadmap, costs


def batch_risk_and_fit(startup_context, features, roadmap, tech_stack, user_profile):
    """
    BATCH 3 of 4: Combines Risk Analysis + Founder Fit + Buildability + Investor Readiness into one call.
    """
    prompt = f"""
You are a startup risk analyst, talent evaluator, CTO, and investor readiness coach.

Startup:
{json.dumps(startup_context, indent=2)}

MVP Features:
{json.dumps(features, indent=2)}

Roadmap:
{json.dumps(roadmap, indent=2)}

Tech Stack:
{json.dumps(tech_stack, indent=2)}

Founder Profile:
{json.dumps(user_profile, indent=2)}

Return a single JSON object with EXACTLY these top-level keys:

"risks": {{
  "technical_risks": [list of strings],
  "product_risks": [list of strings],
  "market_risks": [list of strings],
  "scaling_risks": [list of strings],
  "mitigation_strategies": [list of strings]
}}

"founder_fit": {{
  "founder_market_fit_score": integer (0-100),
  "strengths": [list of strings],
  "weaknesses": [list of strings],
  "recommendations": [list of strings]
}}

"buildability": {{
  "buildability_score": integer (1-10),
  "time_to_mvp_weeks": integer,
  "recommended_team_size": integer,
  "technical_difficulty": string ("Low", "Medium", "High", or "Extreme"),
  "biggest_technical_challenges": [list of strings],
  "biggest_founder_challenges": [list of strings],
  "recommended_mvp_scope": string,
  "build_recommendation": string ("YES", "NO", or "MODIFY")
}}

"investor_readiness": {{
  "investor_readiness_score": integer (0-100),
  "strengths": [list of strings],
  "weaknesses": [list of strings],
  "funding_potential": string
}}

Return ONLY valid JSON. Do NOT include markdown fences.
"""
    result = generate_json(prompt, expected_type=dict, temperature=0.4)

    risks = result.get("risks", {})
    founder_fit = result.get("founder_fit", {})
    buildability = result.get("buildability", {})
    investor_readiness = result.get("investor_readiness", {})

    return risks, founder_fit, buildability, investor_readiness


def batch_strategy(startup_context, founder_fit, investor_readiness):
    """
    BATCH 4 of 4: Combines Revenue Strategy + Launch Strategy + Success Probability into one call.
    """
    prompt = f"""
You are a growth strategist and startup quantitative analyst.

Startup:
{json.dumps(startup_context, indent=2)}

Founder Fit:
{json.dumps(founder_fit, indent=2)}

Investor Readiness:
{json.dumps(investor_readiness, indent=2)}

Return a single JSON object with EXACTLY these top-level keys:

"revenue_strategy": {{
  "revenue_model": string,
  "pricing_tiers": [
    {{
      "tier": string,
      "price": number,
      "features": [list of strings]
    }}
  ],
  "monetization_strategy": string
}}

"launch_strategy": {{
  "first_100_users_plan": [list of strings],
  "marketing_channels": [list of strings],
  "growth_strategy": string
}}

"success_probability": {{
  "success_probability_score": integer (0-100),
  "biggest_opportunity": string,
  "biggest_risk": string,
  "recommendation": string
}}

Return ONLY valid JSON. Do NOT include markdown fences.
"""
    result = generate_json(prompt, expected_type=dict, temperature=0.4)

    revenue_strategy = result.get("revenue_strategy", {})
    launch_strategy = result.get("launch_strategy", {})
    success_probability = result.get("success_probability", {})

    return revenue_strategy, launch_strategy, success_probability


# ==========================================
# MASTER AGENT (Now uses 4 batched calls instead of 14)
# ==========================================

def mvp_planner_agent(startup_idea, user_profile):
    print("\n[Agent 3] Retrieving YC Context...")
    yc_docs = retrieve_yc_context(startup_idea)

    print("[Agent 3] BATCH 1/4 — Product Spec (Features + Tech Stack + DB Schema + APIs)...")
    features, tech_stack, database, apis = batch_product_spec(startup_idea, yc_docs)

    print("[Agent 3] BATCH 2/4 — Execution Plan (UI Design + Roadmap + Cost Estimate)...")
    ui, roadmap, costs = batch_execution_plan(startup_idea, features)

    print("[Agent 3] BATCH 3/4 — Risk & Fit (Risks + Founder Fit + Buildability + Investor Readiness)...")
    risks, founder_fit, buildability, investor_readiness = batch_risk_and_fit(
        startup_idea, features, roadmap, tech_stack, user_profile
    )

    print("[Agent 3] BATCH 4/4 — Strategy (Revenue + Launch + Success Probability)...")
    revenue_strategy, launch_strategy, success_probability = batch_strategy(
        startup_idea, founder_fit, investor_readiness
    )

    return {
        "yc_startups": yc_docs,
        "features": features,
        "tech_stack": tech_stack,
        "database": database,
        "apis": apis,
        "ui": ui,
        "roadmap": roadmap,
        "costs": costs,
        "risks": risks,
        "founder_fit": founder_fit,
        "buildability": buildability,
        "investor_readiness": investor_readiness,
        "revenue_strategy": revenue_strategy,
        "launch_strategy": launch_strategy,
        "success_probability": success_probability,
    }


if __name__ == "__main__":
    startup = {
        "startup_name": "AdaptaLearn",
        "problem": "Students receive generic learning experiences",
        "solution": "AI powered adaptive learning",
        "target_users": "Students and Teachers",
    }

    user_profile = {
        "skills": "Python, React",
        "experience": "Student",
        "budget": "Low",
    }

    result = mvp_planner_agent(startup, user_profile)

    for key, value in result.items():
        print(f"\n{'='*60}\n{key.upper()}\n{'='*60}")
        print(json.dumps(value, indent=2) if isinstance(value, (dict, list)) else value)