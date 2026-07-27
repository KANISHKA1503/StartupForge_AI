import json
from services.gemini import generate_json
from services.vector_store import retrieve_startups


# ==========================================
# FIX 2: AGENT 1 BATCHED (6 calls -> 2 batches)
# ==========================================

def batch_discovery(user_profile, retrieved_docs):
    """
    BATCH A of 2: Combines Intent Analysis + Pattern Discovery + Market Gap Finding
    into a single LLM call. All three share the same YC context and user profile.
    """
    docs_text = "\n\n".join(doc[:400] for doc in retrieved_docs if isinstance(doc, str))[:3000]

    prompt = f"""
You are a startup market analyst and intent extractor.

Founder Profile:
{json.dumps(user_profile, indent=2)}

Similar YC Startups (for market context):
{docs_text}

Perform THREE analyses and return a single JSON object with EXACTLY these top-level keys:

"intent": {{
  "domain": string (e.g. EdTech, FinTech, AI),
  "technology": string (key technologies mentioned or inferred),
  "target_users": string (who the founder wants to serve),
  "startup_type": string (e.g. SaaS, Marketplace, Mobile App),
  "founder_strengths": string (key strengths based on skills and experience)
}}

"patterns": {{
  "common_industries": [list of strings],
  "common_trends": [list of strings],
  "common_business_models": [list of strings],
  "common_customer_segments": [list of strings]
}}

"market_gaps": {{
  "underserved_users": [list of strings],
  "unsolved_problems": [list of strings],
  "market_gaps": [list of strings],
  "emerging_opportunities": [list of strings]
}}

Return ONLY valid JSON. Do NOT include markdown fences.
"""
    result = generate_json(prompt, expected_type=dict, temperature=0.5)
    intent = result.get("intent", {})
    patterns = result.get("patterns", {})
    market_gaps = result.get("market_gaps", {})
    return intent, patterns, market_gaps


def batch_blueprint(user_profile, market_gaps, retrieved_docs):
    """
    BATCH B of 2: Combines Opportunity Generation + Scoring + Blueprint Selection
    into a single LLM call, selecting the best startup idea in one pass.
    """
    docs_text = "\n\n".join(doc[:200] for doc in retrieved_docs if isinstance(doc, str))[:1500]

    prompt = f"""
You are a startup blueprint generator and opportunity evaluator.

Founder Profile:
{json.dumps(user_profile, indent=2)}

Market Gaps & Opportunities:
{json.dumps(market_gaps, indent=2)}

YC Reference Context:
{docs_text}

Perform THREE steps and return a single JSON object with EXACTLY these top-level keys:

"opportunities": [
  list of 5 objects, each with:
  {{
    "opportunity_name": string,
    "problem": string,
    "solution": string,
    "target_users": string,
    "scores": {{
      "innovation": integer (0-100),
      "market_potential": integer (0-100),
      "feasibility": integer (0-100),
      "scalability": integer (0-100)
    }},
    "total_score": integer (average of the 4 scores)
  }}
]

"blueprint": {{
  "startup_name": string (compelling brand name for the BEST scoring opportunity),
  "problem_statement": string,
  "solution": string,
  "target_users": string,
  "revenue_model": string (e.g. B2B SaaS Subscription, Freemium, Usage-based),
  "competitive_advantage": string,
  "why_now": string (market timing),
  "mvp_features": [list of 4-5 specific feature strings],
  "go_to_market_strategy": string,
  "skills": "{user_profile.get('skills', '')}",
  "experience": "{user_profile.get('experience', '')}",
  "budget": "{user_profile.get('budget', '')}",
  "goal": "{user_profile.get('goal', '')}"
}}

Return ONLY valid JSON. Do NOT include markdown fences.
"""
    result = generate_json(prompt, expected_type=dict, temperature=0.5)
    opportunities = result.get("opportunities", [])
    blueprint = result.get("blueprint", {})
    return opportunities, blueprint


# ==========================================
# MASTER AGENT
# ==========================================

def startup_discovery_agent(user_profile):
    print("\n[Agent 1] Retrieving YC Startups for context...")
    retrieved_docs = retrieve_startups(
        query=f"{user_profile.get('interests', '')} {user_profile.get('skills', '')} {user_profile.get('goal', '')}",
        n_results=10
    )

    print("[Agent 1] BATCH A/2 — Intent + Pattern Discovery + Market Gap Analysis...")
    intent, patterns, market_gaps = batch_discovery(user_profile, retrieved_docs)

    print("[Agent 1] BATCH B/2 — Opportunity Generation + Scoring + Blueprint Selection...")
    opportunities, blueprint = batch_blueprint(user_profile, market_gaps, retrieved_docs)

    return {
        "intent": intent,
        "retrieved_startups": retrieved_docs,
        "patterns": patterns,
        "market_gaps": market_gaps,
        "opportunities": opportunities,
        "blueprint": blueprint,
    }


if __name__ == "__main__":
    user_profile = {
        "skills": "Python, React",
        "interests": "AI Education",
        "experience": "Student",
        "budget": "Low",
        "goal": "Build SaaS Startup",
    }

    result = startup_discovery_agent(user_profile)

    print("\n\n========== BLUEPRINT ==========\n")
    print(json.dumps(result["blueprint"], indent=2, ensure_ascii=False))

    with open("startup_blueprint.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    print("\nstartup_blueprint.json saved.")
