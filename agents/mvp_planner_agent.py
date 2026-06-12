
from services.gemini import generate
from services.vector_store import retrieve_startups


def retrieve_yc_context(startup_context):

    query = f"""
    {startup_context['problem']}
    {startup_context['solution']}
    {startup_context['target_users']}
    """

    return retrieve_startups(
        query=query,
        n_results=5
    )


def startup_feature_agent(
    startup_context,
    yc_docs
):

    docs_text = "\n\n".join(yc_docs)

    prompt = f"""
You are an elite startup CTO.

Startup:
{startup_context}

Similar YC Startups:
{docs_text}

Generate:

1. MVP Features
2. Premium Features
3. Differentiators
4. Competitive Advantages

Return ONLY valid JSON.
"""

    return generate(prompt)


def tech_stack_agent(
    startup_context,
    yc_docs
):

    docs_text = "\n\n".join(
        yc_docs
    )

    prompt = f"""
You are a principal startup architect.

Startup:
{startup_context}

Similar YC Startups:
{docs_text}

Prioritize:

- Python
- FastAPI
- PostgreSQL
- ChromaDB

Optimize for:

- Solo founder
- Low budget
- Fast MVP
- High scalability

Avoid enterprise tools.
Avoid expensive services.
Avoid NodeJS unless necessary.

Return ONLY valid JSON.
"""

    return generate(prompt)

def database_agent(
    startup_context,
    features
):

    prompt = f"""
Startup:
{startup_context}

Features:
{features}

Design database schema.

Return ONLY valid JSON.
"""

    return generate(prompt)


def api_agent(
    startup_context,
    features
):

    prompt = f"""
Startup:
{startup_context}

Features:
{features}

Generate REST APIs.

Return ONLY valid JSON.
"""

    return generate(prompt)


def ui_agent(
    startup_context,
    features
):

    prompt = f"""
Startup:
{startup_context}

Features:
{features}

Design UI.

Return ONLY valid JSON.
"""

    return generate(prompt)


def roadmap_agent(
    startup_context,
    features
):

    prompt = f"""
Startup:
{startup_context}

Features:
{features}

Create 4 week roadmap.

Return ONLY valid JSON.
"""

    return generate(prompt)


def cost_agent(
    startup_context,
    tech_stack
):

    prompt = f"""
Startup:
{startup_context}

Tech Stack:
{tech_stack}

Estimate:

1. Development Cost
2. Monthly Cost
3. AI Cost
4. Hosting Cost

Return ONLY valid JSON.
"""

    return generate(prompt)


def risk_agent(
    startup_context,
    features,
    roadmap
):

    prompt = f"""
Startup:
{startup_context}

Features:
{features}

Roadmap:
{roadmap}

Analyze:

1. Technical Risks
2. Product Risks
3. Market Risks
4. Scaling Risks

Return ONLY valid JSON.
"""

    return generate(prompt)


def founder_fit_agent(
    startup_context
):

    prompt = f"""
Startup:
{startup_context}

Evaluate:

1. Founder Market Fit Score
2. Strengths
3. Weaknesses
4. Recommendations

Return ONLY valid JSON.
"""

    return generate(prompt)


def buildability_agent(
    startup_context,
    features,
    tech_stack,
    user_profile
):

    prompt = f"""
You are a senior startup CTO evaluating whether a founder can realistically build this startup.

Startup:
{startup_context}

Features:
{features}

Tech Stack:
{tech_stack}

Founder Profile:
{user_profile}

Evaluate based on:

1. Founder Skills
2. Experience Level
3. Budget Constraints
4. Technical Complexity
5. Team Requirements

Generate:

1. Buildability Score (1-10)
2. Time To MVP
3. Recommended Team Size
4. Technical Difficulty
5. Biggest Technical Challenges
6. Biggest Founder Challenges
7. Recommended MVP Scope
8. Build Recommendation

Scoring Criteria:

- Skills Match
- Experience Match
- Budget Fit
- Development Complexity
- Speed To Launch

Return ONLY valid JSON.
"""

    return generate(prompt)


def investor_readiness_agent(
    startup_context,
    risks
):

    prompt = f"""
Startup:
{startup_context}

Risks:
{risks}

Evaluate:

1. Investor Readiness Score
2. Strengths
3. Weaknesses
4. Funding Potential

Return ONLY valid JSON.
"""

    return generate(prompt)


def revenue_strategy_agent(
    startup_context
):

    prompt = f"""
Startup:
{startup_context}

Generate:

1. Revenue Model
2. Pricing
3. Monetization Strategy

Return ONLY valid JSON.
"""

    return generate(prompt)


def launch_strategy_agent(
    startup_context
):

    prompt = f"""
Startup:
{startup_context}

Generate:

1. First 100 Users Plan
2. Marketing Channels
3. Growth Strategy

Return ONLY valid JSON.
"""

    return generate(prompt)

def success_probability_agent(
    startup_context,
    founder_fit,
    investor_readiness
):

    prompt = f"""
Startup:
{startup_context}

Founder Fit:
{founder_fit}

Investor Readiness:
{investor_readiness}

Evaluate:

1. Success Probability (0-100)
2. Biggest Opportunity
3. Biggest Risk
4. Recommendation

Return ONLY valid JSON.
"""

    return generate(prompt)

def mvp_planner_agent(
    startup_idea,
    user_profile
):

    print("Retrieving YC Startups...")
    yc_docs = retrieve_yc_context(startup_idea)

    print("Generating Features...")
    features = startup_feature_agent(
        startup_idea,
        yc_docs
    )

    print("Designing Tech Stack...")
    tech_stack = tech_stack_agent(
        startup_idea,
        yc_docs
    )

    print("Designing Database...")
    database = database_agent(
        startup_idea,
        features
    )

    print("Generating APIs...")
    apis = api_agent(
        startup_idea,
        features
    )

    print("Designing UI...")
    ui = ui_agent(
        startup_idea,
        features
    )

    print("Creating Roadmap...")
    roadmap = roadmap_agent(
        startup_idea,
        features
    )

    print("Estimating Costs...")
    costs = cost_agent(
        startup_idea,
        tech_stack
    )

    print("Analyzing Risks...")
    risks = risk_agent(
        startup_idea,
        features,
        roadmap
    )

    print("Founder Fit...")
    founder_fit = founder_fit_agent(
        startup_idea
    )

    print("Buildability...")
    buildability = buildability_agent(
    startup_idea,
    features,
    tech_stack,
    user_profile
    )

    print("Investor Readiness...")
    investor_readiness = investor_readiness_agent(
        startup_idea,
        risks
    )

    print("Revenue Strategy...")
    revenue_strategy = revenue_strategy_agent(
        startup_idea
    )

    print("Launch Strategy...")
    launch_strategy = launch_strategy_agent(
        startup_idea
    )
    print("Success Probability...")

    success_probability = success_probability_agent(
    startup_idea,
    founder_fit,
    investor_readiness
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
        "success_probability": success_probability
    }


if __name__ == "__main__":

    startup = {
        "startup_name": "AdaptaLearn",
        "problem": "Students receive generic learning experiences",
        "solution": "AI powered adaptive learning",
        "target_users": "Students and Teachers"
    }

    user_profile = {

    "skills":
    "Python, React",

    "experience":
    "Student",

    "budget":
    "Low"
}

    result = mvp_planner_agent(
    startup,
    user_profile
)

    print("\nRetrieved YC Startups:\n")

    for doc in result["yc_startups"]:

        try:

            name = (
                doc
                .split("Startup Name:")[1]
                .split("Industries:")[0]
                .strip()
            )

            print("•", name)

        except:

            pass

    for key, value in result.items():

        print("\n")
        print("=" * 80)
        print(key.upper())
        print("=" * 80)

        print(value)