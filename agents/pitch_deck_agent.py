import json
from services.gemini import generate_json


def _extract_pitch_context(startup_context, market_validation, architect_report):
    """
    FIX 3: Explicitly extracts the most valuable fields from each agent's output
    instead of blindly truncating the full JSON dump.
    This gives the LLM the richest possible context within a small token budget.
    """
    sc = startup_context if isinstance(startup_context, dict) else {}
    mv = market_validation if isinstance(market_validation, dict) else {}
    ar = architect_report if isinstance(architect_report, dict) else {}

    # From blueprint
    name = sc.get("startup_name", "AI Startup")
    problem = sc.get("problem_statement") or sc.get("problem", "")
    solution = sc.get("solution", "")
    target_users = sc.get("target_users", "")
    revenue_model = sc.get("revenue_model", "")
    competitive_advantage = sc.get("competitive_advantage", "")
    why_now = sc.get("why_now", "")
    mvp_features = sc.get("mvp_features", [])
    go_to_market = sc.get("go_to_market_strategy", "")

    # From market validation (Agent 2)
    scores = mv.get("scores", {})
    market_demand_score = scores.get("market_demand_score", mv.get("market_demand_score", "N/A"))
    opportunity_score = scores.get("opportunity_score", mv.get("opportunity_score", "N/A"))
    founder_fit_score = scores.get("founder_market_fit_score", "N/A")
    validation_summary = mv.get("validation_summary", "")
    build_recommendation = mv.get("build_recommendation", "")
    feasibility = mv.get("feasibility", {})
    time_to_mvp = feasibility.get("time_to_mvp_weeks", "N/A")
    mvp_cost = feasibility.get("mvp_cost_estimate", "N/A")
    primary_customer = mv.get("target_segments", {}).get("primary_customer", target_users)
    beachhead = mv.get("target_segments", {}).get("beachhead_market", "")

    # From architect report (Agent 3)
    features = ar.get("features", {})
    differentiators = features.get("differentiators", []) if isinstance(features, dict) else []
    tech_stack = ar.get("tech_stack", {})
    frontend = tech_stack.get("frontend", "") if isinstance(tech_stack, dict) else ""
    backend = tech_stack.get("backend", "") if isinstance(tech_stack, dict) else ""

    revenue_strategy = ar.get("revenue_strategy", {})
    pricing_tiers = revenue_strategy.get("pricing_tiers", []) if isinstance(revenue_strategy, dict) else []
    pricing_text = ""
    if pricing_tiers:
        pricing_text = " | ".join(
            f"{t.get('tier','')}: ₹{t.get('price','?')}/mo" if isinstance(t.get("price"), (int, float)) and t.get("price", 0) < 1000
            else f"{t.get('tier','')}: ${t.get('price','?')}/mo"
            for t in pricing_tiers[:3] if isinstance(t, dict)
        )

    success = ar.get("success_probability", {})
    success_score = success.get("success_probability_score", "N/A") if isinstance(success, dict) else "N/A"
    biggest_opportunity = success.get("biggest_opportunity", "") if isinstance(success, dict) else ""

    costs = ar.get("costs", {})
    total_cost_inr = costs.get("total_monthly_cost_inr", None) if isinstance(costs, dict) else None
    dev_cost_inr = costs.get("development_cost_inr", None) if isinstance(costs, dict) else None

    return {
        "name": name,
        "problem": problem,
        "solution": solution,
        "target_users": target_users,
        "primary_customer": primary_customer,
        "beachhead": beachhead,
        "revenue_model": revenue_model,
        "competitive_advantage": competitive_advantage,
        "why_now": why_now,
        "mvp_features": mvp_features,
        "go_to_market": go_to_market,
        "differentiators": differentiators,
        "tech_stack_summary": f"Frontend: {frontend} | Backend: {backend}",
        "market_demand_score": market_demand_score,
        "opportunity_score": opportunity_score,
        "founder_fit_score": founder_fit_score,
        "validation_summary": validation_summary,
        "build_recommendation": build_recommendation,
        "time_to_mvp_weeks": time_to_mvp,
        "mvp_cost_estimate": mvp_cost,
        "pricing_tiers_text": pricing_text,
        "success_score": success_score,
        "biggest_opportunity": biggest_opportunity,
        "total_monthly_cost_inr": total_cost_inr,
        "development_cost_inr": dev_cost_inr,
    }


def pitch_deck_agent(startup_context, market_validation, architect_report):
    """
    FIX 3: Richer pitch deck using explicit field extraction.
    Generates a 12-slide investor pitch deck including Financial Projections and Why Now slides.
    """
    ctx = _extract_pitch_context(startup_context, market_validation, architect_report)

    cost_line = ""
    if ctx["total_monthly_cost_inr"]:
        cost_line = f"Monthly burn: ₹{ctx['total_monthly_cost_inr']:,} | Dev cost: ₹{ctx['development_cost_inr']:,}"

    prompt = f"""
You are a world-class YC partner writing an investor pitch deck for a startup.

STARTUP DETAILS:
- Name: {ctx['name']}
- Problem: {ctx['problem']}
- Solution: {ctx['solution']}
- Target Users: {ctx['target_users']}
- Primary Customer: {ctx['primary_customer']}
- Beachhead Market: {ctx['beachhead']}
- Revenue Model: {ctx['revenue_model']}
- Competitive Advantage: {ctx['competitive_advantage']}
- Why Now: {ctx['why_now']}
- MVP Features: {', '.join(str(f) for f in ctx['mvp_features'][:5]) if ctx['mvp_features'] else 'N/A'}
- Differentiators: {', '.join(str(d) for d in ctx['differentiators'][:3]) if ctx['differentiators'] else 'N/A'}
- Tech Stack: {ctx['tech_stack_summary']}
- Go-to-Market: {ctx['go_to_market']}

VALIDATION DATA:
- Market Demand Score: {ctx['market_demand_score']}/100
- Opportunity Score: {ctx['opportunity_score']}/100
- Founder-Market Fit: {ctx['founder_fit_score']}/100
- Success Probability: {ctx['success_score']}/100
- Build Recommendation: {ctx['build_recommendation']}
- Time to MVP: {ctx['time_to_mvp_weeks']} weeks
- Pricing: {ctx['pricing_tiers_text'] or 'Freemium + paid tiers'}
- {cost_line}
- Biggest Opportunity: {ctx['biggest_opportunity']}

Create a high-impact 12-slide investor pitch deck.

Rules:
- EXACTLY 12 slides
- EXACTLY 3 bullet points per slide — data-driven, specific, and punchy
- Use actual numbers from the validation data wherever possible
- DO NOT use vague phrases like "strong demand" — be specific

Slide titles MUST be in this order:
1. Problem
2. Solution
3. Why Now
4. Market Opportunity
5. Target Market
6. Product Demo
7. Competitive Advantage
8. Business Model
9. Financial Projections
10. Traction & Validation
11. Go-to-Market Strategy
12. Investment Ask

Return a JSON object with exactly these keys:
1. "startup_name": string (exactly "{ctx['name']}")
2. "tagline": string (one punchy sentence — max 15 words, avoid generic phrases)
3. "slides": list of exactly 12 slide objects. Each slide object must have:
   - "slide_number": integer (1 to 12)
   - "title": string (use the slide titles listed above, in order)
   - "bullet_points": list of exactly 3 concise strings

Return ONLY valid JSON.
"""
    return generate_json(prompt, expected_type=dict, temperature=0.6)


if __name__ == "__main__":
    startup_context = {
        "startup_name": "MeetBot AI",
        "problem_statement": "Remote teams lose critical context from unrecorded meetings",
        "solution": "Real-time AI transcription and smart meeting summaries with action item extraction",
        "target_users": "Remote teams and distributed companies",
        "revenue_model": "B2B SaaS Subscription",
        "competitive_advantage": "Faster, cheaper, and more accurate than Otter.ai with native action item tracking",
        "why_now": "Post-COVID remote work is now permanent for 40% of knowledge workers",
        "mvp_features": ["Real-time transcription", "AI summaries", "Action item extraction", "Zoom integration"],
        "go_to_market_strategy": "Product-led growth via Slack/Zoom marketplace listings",
    }
    validation = {
        "scores": {"market_demand_score": 85, "opportunity_score": 80, "founder_market_fit_score": 75},
        "validation_summary": "Strong product-market fit in remote collaboration tools segment",
        "build_recommendation": "YES",
        "feasibility": {"time_to_mvp_weeks": 16, "mvp_cost_estimate": "₹3,00,000"},
        "target_segments": {"primary_customer": "Mid-size remote teams", "beachhead_market": "Indian SaaS companies"},
    }
    architect = {
        "tech_stack": {"frontend": "React", "backend": "FastAPI"},
        "features": {"differentiators": ["Multilingual transcription", "Slack native bot", "Granular action tracking"]},
        "revenue_strategy": {"pricing_tiers": [{"tier": "Free", "price": 0}, {"tier": "Pro", "price": 999}, {"tier": "Enterprise", "price": 4999}]},
        "success_probability": {"success_probability_score": 82, "biggest_opportunity": "Growing async-first remote work culture"},
        "costs": {"total_monthly_cost_inr": 6200, "development_cost_inr": 300000},
    }
    result = pitch_deck_agent(startup_context, validation, architect)
    print(json.dumps(result, indent=2, ensure_ascii=False))