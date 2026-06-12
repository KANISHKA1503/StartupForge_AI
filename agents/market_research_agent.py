import json
from services.gemini import generate
from services.vector_store import retrieve_startups

import requests


# ==========================================
# INPUT RESOLVER
# ==========================================

import json
import re

def resolve_input(
    startup_idea=None,
    blueprint=None
):

    if blueprint:

        if isinstance(
            blueprint,
            dict
        ):
            return blueprint

        if isinstance(
            blueprint,
            str
        ):

            try:

                match = re.search(
                    r"```json\s*(.*?)\s*```",
                    blueprint,
                    re.DOTALL
                )

                if match:

                    blueprint_json = (
                        match.group(1)
                    )

                    blueprint = json.loads(
                        blueprint_json
                    )

                    return {

                        "startup_name":
                        blueprint.get(
                            "startup_name",
                            ""
                        ),

                        "problem":
                        blueprint.get(
                            "problem_statement",
                            ""
                        ),

                        "solution":
                        blueprint.get(
                            "solution",
                            ""
                        ),

                        "target_users":
                        blueprint.get(
                            "target_users",
                            ""
                        ),

                        "skills":
                        blueprint.get(
                            "skills",
                            "Unknown"
                        ),

                        "experience":
                        blueprint.get(
                            "experience",
                            "Unknown"
                        ),

                        "budget":
                        blueprint.get(
                            "budget",
                            "Unknown"
                        ),

                        "goal":
                        blueprint.get(
                            "goal",
                            "Unknown"
                        )
                    }

            except Exception as e:

                print(
                    "Blueprint Parse Error:",
                    e
                )

    if startup_idea:

        return startup_idea

    print(
        "Blueprint parsing failed. Using fallback startup."
    )

    return {

        "startup_name":
        "Fallback Startup",

        "problem":
        "Education content creation is time consuming",

        "solution":
        "AI powered content generation",

        "target_users":
        "Teachers",

        "skills":
        "Python, React",

        "experience":
        "Student",

        "budget":
        "Low",

        "goal":
        "Build SaaS Startup"
    }
# ==========================================
# STACKOVERFLOW AGENT
# ==========================================

def stackoverflow_agent(
    query
):

    url = (
        "https://api.stackexchange.com/2.3/search"
    )

    params = {

        "order": "desc",
        "sort": "votes",
        "intitle": query,
        "site": "stackoverflow",
        "pagesize": 30

    }

    response = requests.get(
        url,
        params=params
    )

    data = response.json()

    return data.get(
        "items",
        []
    )


# ==========================================
# HACKERNEWS AGENT
# ==========================================

def hackernews_agent(
    query
):

    url = (
        f"https://hn.algolia.com/api/v1/search?query={query}"
    )

    response = requests.get(
        url
    )

    data = response.json()

    return data.get(
        "hits",
        []
    )


# ==========================================
# YC RETRIEVAL AGENT
# ==========================================

def yc_competitor_agent(
    startup_context
):

    query = f"""
    {startup_context['problem']}
    {startup_context['solution']}
    {startup_context['target_users']}
    """

    startups = retrieve_startups(
        query=query,
        n_results=10
    )

    return startups


# ==========================================
# COMPETITOR AGENT
# ==========================================

def competitor_agent(
    startup_context,
    competitor_text
):

    prompt = f"""
You are a startup competitor analyst.

Founder Profile:

{startup_context}

Relevant YC Startups:

{competitor_text}

Find:

1. Direct Competitors
2. Indirect Competitors
3. Competitor Strengths
4. Competitor Weaknesses
5. Market Gaps
6. Differentiation Opportunities
7. Founder Advantages
8. Founder Disadvantages

Return JSON.
"""

    return generate(prompt)


# ==========================================
# PAIN POINT AGENT
# ==========================================

def pain_point_agent(
    stack_data,
    hn_data
):

    prompt = f"""
You are a startup pain point analyst.

StackOverflow:

{stack_data}

HackerNews:

{hn_data}

Identify:

1. Common Complaints
2. Pain Points
3. Missing Features
4. Frustrations
5. Unsolved Problems

Return JSON.
"""

    return generate(prompt)


# ==========================================
# DEMAND AGENT
# ==========================================

def demand_agent(
    stack_data,
    hn_data,
    startup_context
):

    prompt = f"""
Founder:

{startup_context}

StackOverflow:

{stack_data}

HackerNews:

{hn_data}

Analyze:

1. Market Demand
2. Growth Signals
3. User Interest
4. Emerging Trends
5. Adoption Potential

Also evaluate:

- Founder Fit
- Budget Fit
- Skill Fit

Return JSON.
"""

    return generate(prompt)


# ==========================================
# OPPORTUNITY RANKING AGENT
# ==========================================

def opportunity_ranking_agent(
    startup_context,
    pain_points,
    demand,
    competitors
):

    prompt = f"""
Founder:

{startup_context}

Pain Points:

{pain_points}

Demand:

{demand}

Competitors:

{competitors}

Generate TOP 5 startup opportunities.

For each provide:

1. Opportunity Name
2. Problem
3. Target Users

Score each:

- Market Demand
- Competition
- Founder Fit
- Buildability
- Scalability

Rank from #1 to #5.

Return JSON.
"""

    return generate(prompt)


# ==========================================
# VALIDATION AGENT
# ==========================================

def validation_agent(
    startup_context,
    pain_points,
    competitors,
    demand
):

    prompt = f"""
Founder:

{startup_context}

Pain Points:

{pain_points}

Competitors:

{competitors}

Demand:

{demand}

Evaluate:

1. Market Demand Score (0-100)
2. Competition Score (0-100)
3. Founder-Market Fit Score (0-100)
4. Buildability Score (0-100)
5. Scalability Score (0-100)
6. Execution Risk Score (0-100)
7. Opportunity Score (0-100)

Determine:

1. Can this founder build it?
2. Is the budget sufficient?
3. Time to MVP
4. MVP Cost Estimate

Identify:

1. Primary Customer
2. Secondary Customer
3. Beachhead Market
4. Early Adopters
5. Highest Paying Segment

Provide:

- Validation Summary
- Build Recommendation

Return JSON.
"""

    return generate(prompt)


# ==========================================
# INVESTOR AGENT
# ==========================================

def investor_agent(
    startup_context,
    validation
):

    prompt = f"""
Act as a Y Combinator Partner.

Founder:

{startup_context}

Validation:

{str(validation)[:2500]}

Evaluate:

1. Founder-Market Fit
2. Technical Capability
3. Execution Capability
4. Market Timing
5. Fundability

Would YC invest in THIS founder
building THIS startup?

Provide:

1. Strengths
2. Weaknesses
3. Risks
4. Investment Recommendation

Give:

Investment Score (0-100)

Return JSON.
"""

    return generate(prompt)


# ==========================================
# MASTER AGENT
# ==========================================

def market_research_agent(
    startup_idea=None,
    blueprint=None
):

    startup_context = resolve_input(
        startup_idea,
        blueprint
    )
    print("\nSTARTUP CONTEXT:")
    print(startup_context)
    print(type(startup_context))

    print(
        "Searching StackOverflow..."
    )

    stack_data = stackoverflow_agent(
        startup_context["problem"]
    )

    print(
        "Searching HackerNews..."
    )

    hn_data = hackernews_agent(
        startup_context["problem"]
    )

    print(
        "Retrieving YC Startups..."
    )

    yc_startups = yc_competitor_agent(
        startup_context
    )

    competitor_text = "\n\n".join(
        yc_startups
    )

    print(
        "Analyzing Competitors..."
    )

    competitors = competitor_agent(
        startup_context,
        competitor_text
    )

    print(
        "Finding Pain Points..."
    )

    pain_points = pain_point_agent(
        stack_data,
        hn_data
    )

    print(
        "Analyzing Demand..."
    )

    demand = demand_agent(
        stack_data,
        hn_data,
        startup_context
    )

    print(
        "Ranking Opportunities..."
    )

    ranked_opportunities = (
        opportunity_ranking_agent(
            startup_context,
            pain_points,
            demand,
            competitors
        )
    )

    print(
        "Validating Opportunity..."
    )

    validation = validation_agent(
        startup_context,
        pain_points,
        competitors,
        demand
    )

    print(
        "Getting Investor Feedback..."
    )

    investor_feedback = investor_agent(
        startup_context,
        validation
    )

    return {

        "startup_context":
        startup_context,

        "yc_startups":
        yc_startups,

        "competitors":
        competitors,

        "pain_points":
        pain_points,

        "demand":
        demand,

        "ranked_opportunities":
        ranked_opportunities,

        "validation":
        validation,

        "investor_feedback":
        investor_feedback
    }

# ==========================================
# TEST RUN
# ==========================================

if __name__ == "__main__":

    startup_idea = {

        "startup_name":
        "CurricuLabs AI",

        "problem":
        "Teachers spend too much time creating personalized content",

        "solution":
        "AI powered content generation",

        "target_users":
        "Teachers",

        "skills":
        "Python, React",

        "experience":
        "Student",

        "budget":
        "Low",

        "goal":
        "Build SaaS Startup"
    }

    result = market_research_agent(
        startup_idea=startup_idea
    )

    print("\n" + "=" * 80)
    print("MARKET RESEARCH REPORT")
    print("=" * 80)

    print("\nPAIN POINTS:\n")
    print(result["pain_points"])

    print("\n" + "=" * 80)

    print("\nDEMAND ANALYSIS:\n")
    print(result["demand"])

    print("\n" + "=" * 80)

    print("\nCOMPETITOR ANALYSIS:\n")
    print(result["competitors"])

    print("\n" + "=" * 80)

    print("\nRANKED OPPORTUNITIES:\n")
    print(result["ranked_opportunities"])

    print("\n" + "=" * 80)

    print("\nVALIDATION:\n")
    print(result["validation"])

    print("\n" + "=" * 80)

    print("\nINVESTOR FEEDBACK:\n")
    print(result["investor_feedback"])

    print("\n" + "=" * 80)