from services.gemini import generate


def pitch_deck_agent(

    startup_context,

    market_validation,

    architect_report

):

    prompt = f"""
You are a YC partner and startup investor.

Startup:

{startup_context}

Market Validation:

{market_validation}

Architecture Report:

{architect_report}

Create a concise investor pitch deck.

Rules:

- Maximum 10 slides
- Maximum 3 bullet points per slide
- Keep answers short
- Return compact JSON only

Generate:

1. Startup Name
2. Problem
3. Solution
4. Market Opportunity
5. Competitive Landscape
6. Product Overview
7. Business Model
8. Go To Market Strategy
9. Development Roadmap
10. Financial Projections
11. Funding Ask

Return ONLY valid JSON.
"""

    return generate(prompt)
if __name__ == "__main__":

    startup_context = {

        "startup_name":
        "AdaptaLearn",

        "problem":
        "Students receive generic learning experiences",

        "solution":
        "AI powered adaptive learning",

        "target_users":
        "Students and Teachers"
    }

    result = pitch_deck_agent(

        startup_context,

        "Validated Market",

        "Architect Report"
    )

    print(result)