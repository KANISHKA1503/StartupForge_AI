
from services.gemini import generate
from services.vector_store import retrieve_startups

import json


# ==========================================
# INTENT ANALYZER
# ==========================================

def analyze_intent(user_input):

    prompt = f"""
You are an intent analyzer.

Extract:

1. Domain
2. Technology
3. Target Users
4. Startup Type
5. Founder Strengths

Return ONLY JSON.

Input:

{user_input}
"""

    return generate(prompt)


# ==========================================
# RETRIEVAL AGENT
# ==========================================

def startup_retrieval_agent(intent):

    return retrieve_startups(intent)


# ==========================================
# PATTERN DISCOVERY AGENT
# ==========================================

def discover_patterns(
    retrieved_docs,
    user_profile
):

    docs_text = "\n\n".join(
        doc[:500]
        for doc in retrieved_docs
    )

    prompt = f"""
You are a startup trend analyst.

User Profile:

{user_profile}

Analyze startups while considering:

- User skills
- User experience
- User budget
- User goal

Analyze these startups.

Find:

1. Common industries
2. Common trends
3. Common business models
4. Common customer segments

Return JSON.

{docs_text}
"""

    return generate(prompt)


# ==========================================
# MARKET GAP AGENT
# ==========================================

def find_market_gaps(
    patterns,
    user_profile
):

    prompt = f"""
You are a market analyst.

Patterns:

{patterns}

User Profile:

{user_profile}

Find:

1. Underserved users
2. Unsolved problems
3. Market gaps
4. Emerging opportunities

Return JSON.
"""

    return generate(prompt)


# ==========================================
# OPPORTUNITY GENERATOR AGENT
# ==========================================

def generate_opportunities(
    gaps,
    user_profile
):

    prompt = f"""
You are a startup opportunity generator.

Market Gaps:

{gaps}

User Profile:

{user_profile}

Generate opportunities that match:

- Skills
- Budget
- Experience
- Goal

Generate 10 startup opportunities.

For each provide:

- Problem
- Solution
- Target Users

Return JSON.
"""

    return generate(prompt)


# ==========================================
# OPPORTUNITY SCORING AGENT
# ==========================================

def score_opportunities(
    opportunities
):

    prompt = f"""
You are a startup evaluator.

Evaluate opportunities.

Score:

- Innovation
- Market Potential
- Feasibility
- Scalability

Each out of 100.

Return JSON.

{opportunities}
"""

    return generate(prompt)


# ==========================================
# BLUEPRINT AGENT
# ==========================================

def generate_blueprint(
    opportunities,
    scores,
    user_profile
):

    prompt = f"""
You are a startup blueprint generator.

Opportunities:

{opportunities}

Scores:

{scores}

User Profile:

{user_profile}

Select the BEST opportunity.

Generate:

1. Startup Name
2. Problem Statement
3. Solution
4. Target Users
5. Revenue Model
6. Competitive Advantage
7. Why Now
8. MVP Features
9. Go-To-Market Strategy

Return JSON.
"""

    return generate(prompt)


# ==========================================
# MASTER AGENT
# ==========================================

def startup_discovery_agent(
    user_profile
):

    print("\n[1] Analyzing Intent...")

    intent = analyze_intent(
        user_profile
    )

    print("\n[2] Retrieving Startups...")

    startups = startup_retrieval_agent(
        intent
    )

    print("\n[3] Finding Patterns...")

    patterns = discover_patterns(
        startups,
        user_profile
    )

    print("\n[4] Finding Market Gaps...")

    gaps = find_market_gaps(
        patterns,
        user_profile
    )

    print("\n[5] Generating Opportunities...")

    opportunities = generate_opportunities(
        gaps,
        user_profile
    )

    print("\n[6] Scoring Opportunities...")

    scores = score_opportunities(
        opportunities
    )

    print("\n[7] Generating Blueprint...")

    blueprint = generate_blueprint(
        opportunities,
        scores,
        user_profile
    )

    result = {
        "intent": intent,
        "retrieved_startups": startups,
        "patterns": patterns,
        "market_gaps": gaps,
        "opportunities": opportunities,
        "scores": scores,
        "blueprint": blueprint
    }

    return result


# ==========================================
# TEST RUN
# ==========================================

if __name__ == "__main__":

    user_profile = {
        "skills": "Python, React",
        "interests": "AI Education",
        "experience": "Student",
        "budget": "Low",
        "goal": "Build SaaS Startup"
    }

    result = startup_discovery_agent(
        user_profile
    )

    print("\n\n========== BLUEPRINT ==========\n")
    print(result["blueprint"])

    with open(
        "startup_blueprint.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        "\nstartup_blueprint.json saved successfully."
    )

