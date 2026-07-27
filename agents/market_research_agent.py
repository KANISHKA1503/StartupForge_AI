import json
import re
import requests
from services.gemini import generate, generate_json, parse_json_from_string
from services.vector_store import retrieve_startups, retrieve_similar_user_startups, retrieve_india_funding, load_india_funding_data

# Pre-load India funding DB on agent import (non-blocking, skips if already loaded)
try:
    load_india_funding_data()
except Exception:
    pass


# ==========================================
# INPUT RESOLVER
# ==========================================

def resolve_input(startup_idea=None, blueprint=None):
    if blueprint:
        if isinstance(blueprint, str):
            parsed = parse_json_from_string(blueprint)
            if isinstance(parsed, dict):
                blueprint = parsed
        
        if isinstance(blueprint, dict):
            return {
                "startup_name": blueprint.get("startup_name", "AI Startup"),
                "problem": blueprint.get("problem_statement") or blueprint.get("problem", ""),
                "solution": blueprint.get("solution", ""),
                "target_users": blueprint.get("target_users", ""),
                "skills": blueprint.get("skills", "Python, React"),
                "experience": blueprint.get("experience", "Student"),
                "budget": blueprint.get("budget", "Low"),
                "goal": blueprint.get("goal", "Build SaaS Startup"),
            }

    if startup_idea and isinstance(startup_idea, dict):
        return {
            "startup_name": startup_idea.get("startup_name", "AI Startup"),
            "problem": startup_idea.get("problem", ""),
            "solution": startup_idea.get("solution", ""),
            "target_users": startup_idea.get("target_users", ""),
            "skills": startup_idea.get("skills", "Python, React"),
            "experience": startup_idea.get("experience", "Student"),
            "budget": startup_idea.get("budget", "Low"),
            "goal": startup_idea.get("goal", "Build SaaS Startup"),
        }

    print("[WARN] Blueprint parsing failed or missing. Using fallback startup.")
    return {
        "startup_name": "Fallback Startup",
        "problem": "Education content creation is time consuming",
        "solution": "AI powered content generation",
        "target_users": "Teachers",
        "skills": "Python, React",
        "experience": "Student",
        "budget": "Low",
        "goal": "Build SaaS Startup",
    }


def clean_search_query(text):
    """
    Extracts 2-3 core domain keywords from a long problem statement or text
    so that APIs (StackOverflow, HackerNews, GitHub) return meaningful hits.
    """
    if not text:
        return "AI startup"
    
    stopwords = {
        "i", "me", "my", "we", "our", "you", "your", "he", "him", "his", "she", "her",
        "it", "its", "they", "them", "their", "what", "which", "who", "whom", "this",
        "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the",
        "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by",
        "for", "with", "about", "against", "between", "into", "through", "during",
        "before", "after", "above", "below", "to", "from", "up", "down", "in", "out",
        "on", "off", "over", "under", "again", "further", "then", "once", "here", "there",
        "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same",
        "so", "than", "too", "very", "can", "will", "just", "should", "now", "spend",
        "much", "time", "creating", "receive", "generic", "experiences", "powered", "system"
    }
    
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    keywords = [w for w in words if w not in stopwords]
    
    if not keywords:
        return "AI tools"
    
    seen = set()
    distinct_kw = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            distinct_kw.append(w)
        if len(distinct_kw) == 3:
            break
            
    return " ".join(distinct_kw)


# ==========================================
# STACKOVERFLOW AGENT
# ==========================================

def stackoverflow_agent(query_str):
    search_terms = clean_search_query(query_str)
    url = "https://api.stackexchange.com/2.3/search"
    params = {
        "order": "desc",
        "sort": "votes",
        "intitle": search_terms,
        "site": "stackoverflow",
        "pagesize": 15,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data.get("items", [])
    except Exception as e:
        print(f"[stackoverflow_agent] Search failed for '{search_terms}': {e}")
        return []


# ==========================================
# HACKERNEWS AGENT
# ==========================================

def hackernews_agent(query_str):
    search_terms = clean_search_query(query_str)
    url = f"https://hn.algolia.com/api/v1/search?query={requests.utils.quote(search_terms)}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("hits", [])
    except Exception as e:
        print(f"[hackernews_agent] Search failed for '{search_terms}': {e}")
        return []


# ==========================================
# LIVE WEB COMPETITOR AGENTS (HYBRID RETRIEVAL)
# ==========================================

def github_competitor_agent(query_str):
    """
    Searches live GitHub open-source repositories to find existing tools
    and open-source competitors building in this exact domain.
    """
    search_terms = clean_search_query(query_str)
    url = f"https://api.github.com/search/repositories?q={requests.utils.quote(search_terms)}&sort=stars&order=desc&per_page=5"
    
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        items = data.get("items", [])
        
        competitors = []
        for item in items:
            name = item.get("full_name", "")
            desc = item.get("description", "No description")
            stars = item.get("stargazers_count", 0)
            url_str = item.get("html_url", "")
            competitors.append(f"[GitHub Open Source Tool] {name}: {desc} (Stars: {stars}, URL: {url_str})")
        return competitors
    except Exception as e:
        print(f"[github_competitor_agent] GitHub search failed for '{search_terms}': {e}")
        return []


def show_hn_competitor_agent(query_str):
    """
    Searches live HackerNews 'Show HN' launches to find real startups
    and products launched by developers in this market.
    """
    search_terms = clean_search_query(query_str)
    url = f"https://hn.algolia.com/api/v1/search?query=Show+HN+{requests.utils.quote(search_terms)}&tags=show_hn&hitsPerPage=5"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        hits = data.get("hits", [])
        
        launches = []
        for hit in hits:
            title = hit.get("title", "")
            points = hit.get("points", 0)
            url_str = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            launches.append(f"[Show HN Startup Launch] {title} (Points: {points}, URL: {url_str})")
        return launches
    except Exception as e:
        print(f"[show_hn_competitor_agent] Show HN search failed for '{search_terms}': {e}")
        return []


def summarize_competitor_sources(startup_context, yc_startups, memory_startups, github_tools, hn_launches):
    """
    FIX 3: Summarizes each retrieval source independently before merging.
    Prevents context overflow when the combined competitor text exceeds LLM input limits.
    Each source is condensed to a compact, structured bullet list.
    """
    name = startup_context.get('startup_name', 'the startup')
    problem = startup_context.get('problem', '')

    # YC startups: extract name + one-liner only (skip long descriptions)
    yc_bullets = []
    for doc in yc_startups:
        if not isinstance(doc, str):
            continue
        try:
            sname = doc.split("Startup Name:")[1].split("\n")[0].strip()
            one_liner = ""
            if "One Liner:" in doc:
                one_liner = doc.split("One Liner:")[1].split("\n")[0].strip()
            yc_bullets.append(f"• [YC] {sname}: {one_liner}")
        except Exception:
            yc_bullets.append(f"• [YC] {doc[:120].strip()}")

    # Memory DB: already compact strings — just truncate
    memory_bullets = [f"• [PAST PROJECT] {doc[:150].strip()}" for doc in memory_startups if isinstance(doc, str)]

    # GitHub + Show HN: already one-line strings
    github_bullets = [f"• {item[:150]}" for item in github_tools if isinstance(item, str)]
    hn_bullets = [f"• {item[:150]}" for item in hn_launches if isinstance(item, str)]

    sections = []
    if yc_bullets:
        sections.append("=== YC Funded Startups ===\n" + "\n".join(yc_bullets[:6]))
    if memory_bullets:
        sections.append("=== Past HackArena Projects ===\n" + "\n".join(memory_bullets[:3]))
    if github_bullets:
        sections.append("=== GitHub Open Source Tools ===\n" + "\n".join(github_bullets[:5]))
    if hn_bullets:
        sections.append("=== Show HN Startup Launches ===\n" + "\n".join(hn_bullets[:5]))

    summary = f"Competitor landscape for '{name}' (Problem: {problem[:80]})\n\n"
    summary += "\n\n".join(sections)
    return summary


def yc_competitor_agent(startup_context):
    """
    HYBRID COMPETITOR RETRIEVAL:
    Combines Local YC funded startups + Memory DB past user startups + 
    Live GitHub Open Source Tools + Live Show HN Startup Launches.
    Sources are then summarized per-source to avoid context overflow.
    """
    query = f"""
    {startup_context.get('problem', '')}
    {startup_context.get('solution', '')}
    {startup_context.get('target_users', '')}
    """
    
    print(" -> [Hybrid Retrieval] Querying Local YC Funded Startups...")
    yc_startups = retrieve_startups(query=query, n_results=7)
    
    print(" -> [Hybrid Retrieval] Querying Memory DB (Past HackArena User Projects)...")
    memory_startups = retrieve_similar_user_startups(query=query, n_results=3)
    
    print(" -> [Hybrid Retrieval] Querying Live GitHub Open Source Competitors...")
    github_tools = github_competitor_agent(query)
    
    print(" -> [Hybrid Retrieval] Querying Live Show HN Startup Launches...")
    hn_launches = show_hn_competitor_agent(query)

    print(" -> [Hybrid Retrieval] Summarizing competitor sources to prevent context overflow...")
    competitor_summary = summarize_competitor_sources(
        startup_context, yc_startups, memory_startups, github_tools, hn_launches
    )

    # Return raw list for storage in result, plus summary for LLM prompts
    combined_competitors = yc_startups + memory_startups + github_tools + hn_launches
    return combined_competitors, competitor_summary


# ==========================================
# COMPETITOR AGENT
# ==========================================

def competitor_agent(startup_context, competitor_summary):
    prompt = f"""
You are a startup competitor analyst.

Founder Profile & Idea:
{json.dumps(startup_context, indent=2)}

Hybrid Competitor Intelligence (YC Startups, Community Projects, GitHub Tools, Show HN Launches):
{competitor_summary}

Analyze competitors across commercial startups and open-source tools. Return a JSON object with exactly these keys:
1. "direct_competitors": list of strings
2. "indirect_competitors": list of strings
3. "competitor_strengths": list of strings
4. "competitor_weaknesses": list of strings
5. "market_gaps": list of strings
6. "differentiation_opportunities": list of strings
7. "founder_advantages": list of strings
8. "founder_disadvantages": list of strings

Return ONLY valid JSON.
"""
    return generate_json(prompt, expected_type=dict)


# ==========================================
# PAIN POINT AGENT
# ==========================================

def pain_point_agent(stack_data, hn_data):
    stack_summary = [item.get("title", "") for item in stack_data[:10]]
    hn_summary = [item.get("title", "") for item in hn_data[:10]]

    prompt = f"""
You are a startup pain point analyst.

StackOverflow discussions:
{json.dumps(stack_summary, indent=2)}

HackerNews discussions:
{json.dumps(hn_summary, indent=2)}

Identify key user pain points from these developer and tech communities. Return a JSON object with exactly these keys:
1. "common_complaints": list of strings
2. "pain_points": list of strings
3. "missing_features": list of strings
4. "frustrations": list of strings
5. "unsolved_problems": list of strings

Return ONLY valid JSON.
"""
    return generate_json(prompt, expected_type=dict)


# ==========================================
# DEMAND AGENT
# ==========================================

def demand_agent(stack_data, hn_data, startup_context):
    stack_summary = [item.get("title", "") for item in stack_data[:10]]
    hn_summary = [item.get("title", "") for item in hn_data[:10]]

    prompt = f"""
You are a market demand analyst.

Founder & Startup Context:
{json.dumps(startup_context, indent=2)}

StackOverflow discussions:
{json.dumps(stack_summary, indent=2)}

HackerNews discussions:
{json.dumps(hn_summary, indent=2)}

Analyze market demand and founder fit. Return a JSON object with exactly these keys:
1. "market_demand": string description
2. "growth_signals": list of strings
3. "user_interest": string ("High", "Medium", or "Low")
4. "emerging_trends": list of strings
5. "adoption_potential": string description
6. "founder_fit": string description
7. "budget_fit": string description
8. "skill_fit": string description

Return ONLY valid JSON.
"""
    return generate_json(prompt, expected_type=dict)


# ==========================================
# OPPORTUNITY RANKING AGENT
# ==========================================

def opportunity_ranking_agent(startup_context, pain_points, demand, competitors):
    prompt = f"""
You are an opportunity ranking analyst.

Founder & Idea:
{json.dumps(startup_context, indent=2)}

Pain Points:
{json.dumps(pain_points, indent=2)}

Demand:
{json.dumps(demand, indent=2)}

Competitors:
{json.dumps(competitors, indent=2)}

Generate the TOP 5 startup opportunities derived from this research.
Return a JSON object with a single key "ranked_opportunities" containing a list of 5 objects ranked from #1 to #5.
Each object must have:
- "rank": integer (1 to 5)
- "opportunity_name": string
- "problem": string
- "target_users": string
- "scores": object with integer keys out of 100 for "market_demand", "competition", "founder_fit", "buildability", "scalability"

Return ONLY valid JSON.
"""
    result = generate_json(prompt, expected_type=dict)
    return result.get("ranked_opportunities", []) if isinstance(result, dict) else result


# ==========================================
# VALIDATION AGENT
# ==========================================

def validation_agent(startup_context, pain_points, competitors, demand):
    prompt = f"""
You are a startup validation agent.

Founder & Idea:
{json.dumps(startup_context, indent=2)}

Pain Points:
{json.dumps(pain_points, indent=2)}

Competitors:
{json.dumps(competitors, indent=2)}

Demand:
{json.dumps(demand, indent=2)}

Evaluate the startup concept and return a comprehensive JSON validation report with exactly these keys:
1. "scores": object with integer scores (0-100) for:
   - "market_demand_score"
   - "competition_score"
   - "founder_market_fit_score"
   - "buildability_score"
   - "scalability_score"
   - "execution_risk_score"
   - "opportunity_score"
2. "feasibility": object with keys:
   - "can_founder_build": boolean
   - "budget_sufficient": boolean
   - "time_to_mvp_weeks": integer
   - "mvp_cost_estimate": string
3. "target_segments": object with keys:
   - "primary_customer": string
   - "secondary_customer": string
   - "beachhead_market": string
   - "early_adopters": string
   - "highest_paying_segment": string
4. "validation_summary": string
5. "build_recommendation": string ("YES", "NO", or "MODIFY")

Return ONLY valid JSON.
"""
    return generate_json(prompt, expected_type=dict)


# ==========================================
# INVESTOR AGENT
# ==========================================

def investor_agent(startup_context, validation):
    # FIX 5: Retrieve real Indian funding benchmarks for this industry
    domain_query = f"{startup_context.get('problem', '')} {startup_context.get('target_users', '')}"
    india_rounds = retrieve_india_funding(domain_query, n_results=4)
    india_funding_text = "\n".join(india_rounds) if india_rounds else "No comparable Indian funding data found."

    prompt = f"""
Act as a Y Combinator Partner evaluating a startup, with knowledge of the Indian startup ecosystem.

Founder & Idea:
{json.dumps(startup_context, indent=2)}

Validation Data:
{json.dumps(validation, indent=2)}

Comparable Indian Startup Funding Rounds (for grounded benchmarks):
{india_funding_text}

Evaluate whether YC or an Indian VC would invest in this founder.
Use the Indian funding data to provide realistic funding amount suggestions in INR.
Return a JSON object with exactly these keys:
1. "investment_score": integer (0-100)
2. "evaluation": object with string evaluations for:
   - "founder_market_fit"
   - "technical_capability"
   - "execution_capability"
   - "market_timing"
   - "fundability"
3. "strengths": list of strings
4. "weaknesses": list of strings
5. "risks": list of strings
6. "investment_recommendation": string
7. "comparable_indian_startups": list of strings (names of similar Indian startups that raised funding)
8. "suggested_raise_inr": string (realistic raise amount in INR based on comparable rounds)

Return ONLY valid JSON.
"""
    return generate_json(prompt, expected_type=dict)


# ==========================================
# MASTER AGENT
# ==========================================

def market_research_agent(startup_idea=None, blueprint=None):
    startup_context = resolve_input(startup_idea, blueprint)
    print("\nSTARTUP CONTEXT:")
    print(json.dumps(startup_context, indent=2))

    print("Searching StackOverflow...")
    stack_data = stackoverflow_agent(startup_context.get("problem", ""))

    print("Searching HackerNews...")
    hn_data = hackernews_agent(startup_context.get("problem", ""))

    print("Retrieving Hybrid Competitor Intelligence (YC + Memory + GitHub + Show HN)...")
    yc_startups, competitor_summary = yc_competitor_agent(startup_context)

    print("Analyzing Competitors (using per-source summarized context)...")
    competitors = competitor_agent(startup_context, competitor_summary)

    print("Finding Pain Points...")
    pain_points = pain_point_agent(stack_data, hn_data)

    print("Analyzing Demand...")
    demand = demand_agent(stack_data, hn_data, startup_context)

    print("Ranking Opportunities...")
    ranked_opportunities = opportunity_ranking_agent(startup_context, pain_points, demand, competitors)

    print("Validating Opportunity...")
    validation = validation_agent(startup_context, pain_points, competitors, demand)

    print("Getting Investor Feedback...")
    investor_feedback = investor_agent(startup_context, validation)

    return {
        "startup_context": startup_context,
        "yc_startups": yc_startups,
        "competitors": competitors,
        "pain_points": pain_points,
        "demand": demand,
        "ranked_opportunities": ranked_opportunities,
        "validation": validation,
        "investor_feedback": investor_feedback,
    }


# ==========================================
# TEST RUN
# ==========================================

if __name__ == "__main__":
    startup_idea = {
        "startup_name": "CurricuLabs AI",
        "problem": "Teachers spend too much time creating personalized content",
        "solution": "AI powered content generation",
        "target_users": "Teachers",
        "skills": "Python, React",
        "experience": "Student",
        "budget": "Low",
        "goal": "Build SaaS Startup",
    }

    result = market_research_agent(startup_idea=startup_idea)

    print("\n" + "=" * 80)
    print("MARKET RESEARCH REPORT")
    print("=" * 80)

    print("\nPAIN POINTS:\n", json.dumps(result["pain_points"], indent=2))
    print("\nDEMAND ANALYSIS:\n", json.dumps(result["demand"], indent=2))
    print("\nCOMPETITOR ANALYSIS:\n", json.dumps(result["competitors"], indent=2))
    print("\nRANKED OPPORTUNITIES:\n", json.dumps(result["ranked_opportunities"], indent=2))
    print("\nVALIDATION:\n", json.dumps(result["validation"], indent=2))
    print("\nINVESTOR FEEDBACK:\n", json.dumps(result["investor_feedback"], indent=2))