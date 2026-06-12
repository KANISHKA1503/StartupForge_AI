from agents.agent1 import startup_discovery_agent
from agents.market_research_agent import market_research_agent
from agents.mvp_planner_agent import mvp_planner_agent
from agents.pitch_deck_agent import (
    pitch_deck_agent
)

def main():

    user_profile = {

        "skills":
        "Python, React",

        "interests":
        "AI Education",

        "experience":
        "Student",

        "budget":
        "Low",

        "goal":
        "Build SaaS Startup"
    }

    print("\n" + "=" * 80)
    print("RUNNING AGENT 1")
    print("=" * 80)

    agent1_result = startup_discovery_agent(
        user_profile
    )

    blueprint = agent1_result.get(
        "blueprint"
    )

    print("\nBLUEPRINT TYPE:")
    print(type(blueprint))

    print("\nBLUEPRINT:")
    print(blueprint)

    print("\n" + "=" * 80)
    print("RUNNING AGENT 2")
    print("=" * 80)

    fallback_startup = {

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

    agent2_result = market_research_agent(
    startup_idea=fallback_startup
    )

    print("\n" + "=" * 80)
    print("FINAL VALIDATED STARTUP")
    print("=" * 80)

    print("\nSTARTUP BLUEPRINT:\n")
    print(blueprint)

    print("\n" + "=" * 80)

    print("\nMARKET VALIDATION:\n")
    print(
        agent2_result.get(
            "validation",
            "No validation available"
        )
    )

    print("\n" + "=" * 80)

    print("\nINVESTOR FEEDBACK:\n")
    print(
        agent2_result.get(
            "investor_feedback",
            "No investor feedback available"
        )
    )

    print("\n" + "=" * 80)

    # ==========================
    # AGENT 3
    # ==========================

    print("\n" + "=" * 80)
    print("RUNNING AGENT 3")
    print("=" * 80)

    startup_context = {
    "startup_name": "Generated Startup",
    "problem": str(blueprint),
    "solution": str(blueprint),
    "target_users": "Students"
}   

    agent3_result = mvp_planner_agent(
        startup_context ,user_profile
    )

    print("\n" + "=" * 80)
    print("STARTUP ARCHITECT REPORT")
    print("=" * 80)

    for key, value in agent3_result.items():

        print("\n")
        print("=" * 80)
        print(key.upper())
        print("=" * 80)

        print(value)

    print("\n")
    print("=" * 80)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 80)
    
    print("\n" + "=" * 80)
    
    print("RUNNING AGENT 4")
    print("=" * 80)
    
    architect_summary = {

    "features":
    agent3_result.get(
        "features",
        ""
    ),

    "revenue_strategy":
    agent3_result.get(
        "revenue_strategy",
        ""
    ),

    "success_probability":
    agent3_result.get(
        "success_probability",
        ""
    )
}
    pitch_deck = pitch_deck_agent(

    startup_context,

    agent2_result.get(
        "validation",
        ""
    ),

    architect_summary
)

    print("\nPITCH DECK\n")
    print(pitch_deck)

if __name__ == "__main__":
    main()