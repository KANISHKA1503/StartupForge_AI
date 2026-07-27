import sys
import json
import argparse
import threading
import itertools
import time as _time

# Force UTF-8 output on Windows terminals (fixes ₹ and other Unicode symbols)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from agents.agent1 import startup_discovery_agent
from agents.market_research_agent import market_research_agent
from agents.mvp_planner_agent import mvp_planner_agent
from agents.pitch_deck_agent import pitch_deck_agent
from services.gemini import generate_json
from services.vector_store import store_user_startup
from services.export import export_pitch_deck_html


# ==========================================
# FIX 6: LIVE PROGRESS SPINNER
# ==========================================

class Spinner:
    """A lightweight terminal spinner for long-running LLM steps."""
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message="Working"):
        self.message = message
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        for frame in itertools.cycle(self.FRAMES):
            if self._stop_event.is_set():
                break
            try:
                sys.stdout.write(f"\r  {frame}  {self.message}...")
                sys.stdout.flush()
            except Exception:
                pass
            _time.sleep(0.1)
        try:
            sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
            sys.stdout.flush()
        except Exception:
            pass

    def start(self):
        self._thread.start()
        return self

    def stop(self, done_msg=""):
        self._stop_event.set()
        self._thread.join()
        if done_msg:
            try:
                print(f"  ✓  {done_msg}")
            except UnicodeEncodeError:
                print(f"  OK  {done_msg}")

    def __enter__(self):
        return self.start()

    def __exit__(self, *_):
        self.stop()



def structure_user_idea(idea_text, user_profile, startup_name=None, problem=None, solution=None, target_users=None):
    """
    Medium Fix 1: Takes a user's custom startup idea and structures it into a standardized
    blueprint dictionary. User-provided fields (name, problem, solution, target_users)
    are ALWAYS preserved verbatim — the LLM only fills in the missing enrichment fields.
    """
    # Lock user-provided values upfront — these will NOT be overridden by the LLM
    locked_name = startup_name.strip() if startup_name and startup_name.strip() else None
    locked_problem = problem.strip() if problem and problem.strip() else None
    locked_solution = solution.strip() if solution and solution.strip() else None
    locked_users = target_users.strip() if target_users and target_users.strip() else None

    prompt = f"""
You are a startup architect helping enrich a founder's existing startup idea.
Do NOT rewrite or change any field marked as [PROVIDED BY FOUNDER]. Only generate missing fields.

Founder-Provided Details:
- Startup Name: {locked_name or '[NOT PROVIDED - suggest a name]'}
- Problem Statement: {locked_problem or '[NOT PROVIDED - infer from idea summary]'}
- Solution: {locked_solution or '[NOT PROVIDED - infer from idea summary]'}
- Target Users: {locked_users or '[NOT PROVIDED - infer from context]'}
- Idea Summary: {idea_text or 'Not specified'}

Founder Profile:
{json.dumps(user_profile, indent=2)}

Return a JSON object with exactly these keys:
1. "startup_name": string (use provided name exactly, or suggest one if not provided)
2. "problem_statement": string (use provided value exactly, or infer from idea)
3. "solution": string (use provided value exactly, or infer from idea)
4. "target_users": string (use provided value exactly, or infer)
5. "revenue_model": string (e.g., B2B SaaS Subscription, Usage-based, Freemium)
6. "competitive_advantage": string (why this beats existing tools)
7. "why_now": string (market timing rationale)
8. "mvp_features": list of 4-5 specific feature strings (based on the idea)
9. "go_to_market_strategy": string (first channels to acquire users)
10. "skills": "{user_profile.get('skills', '')}"
11. "experience": "{user_profile.get('experience', '')}"
12. "budget": "{user_profile.get('budget', '')}"
13. "goal": "{user_profile.get('goal', '')}"

Return ONLY valid JSON.
"""
    result = generate_json(prompt, expected_type=dict)

    if isinstance(result, dict) and result.get("startup_name"):
        # Medium Fix 1: Force-override any LLM-changed fields with the user's original locked values
        if locked_name:
            result["startup_name"] = locked_name
        if locked_problem:
            result["problem_statement"] = locked_problem
        if locked_solution:
            result["solution"] = locked_solution
        if locked_users:
            result["target_users"] = locked_users
        # Always stamp founder profile fields from actual user input
        result["skills"] = user_profile.get("skills", "")
        result["experience"] = user_profile.get("experience", "")
        result["budget"] = user_profile.get("budget", "")
        result["goal"] = user_profile.get("goal", "")
        return result

    # Fallback if LLM fails entirely — use user-provided fields directly
    return {
        "startup_name": locked_name or "Custom AI Startup",
        "problem_statement": locked_problem or f"Solving key efficiency challenges in: {idea_text}",
        "solution": locked_solution or idea_text or "AI-powered automated platform",
        "target_users": locked_users or "Industry Professionals",
        "revenue_model": "SaaS Subscription Tiered Pricing",
        "competitive_advantage": "AI automation and domain-specific workflow tailoring",
        "why_now": "Increasing demand for automated productivity solutions",
        "mvp_features": ["Core processing engine", "Interactive user dashboard", "API integrations"],
        "go_to_market_strategy": "Community marketing, direct B2B outreach, and partnerships",

        "skills": user_profile.get("skills", ""),
        "experience": user_profile.get("experience", ""),
        "budget": user_profile.get("budget", ""),
        "goal": user_profile.get("goal", ""),
    }


def get_user_input():
    """
    Dynamically obtains user profile AND optional custom startup idea
    from command-line arguments, JSON file, or interactive CLI prompts.
    """
    parser = argparse.ArgumentParser(description="HackArena 2.0 - Autonomous Startup Pipeline")
    parser.add_argument("--skills", type=str, help="Founder skills (e.g., Python, React)")
    parser.add_argument("--interests", type=str, help="Founder interests/domain (e.g., AI Education)")
    parser.add_argument("--experience", type=str, help="Experience level (e.g., Student, Senior Engineer)")
    parser.add_argument("--budget", type=str, help="Budget level (e.g., Low, Medium, High)")
    parser.add_argument("--goal", type=str, help="Founder goal (e.g., Build SaaS Startup)")
    parser.add_argument("--file", type=str, help="Path to JSON file containing user profile and optional idea")
    parser.add_argument("--default", action="store_true", help="Use default profile without prompting")
    
    # Custom startup idea arguments (to skip Agent 1 and start at Agent 2)
    parser.add_argument("--idea", type=str, help="Custom startup idea summary (skips Agent 1)")
    parser.add_argument("--startup-name", type=str, help="Custom startup brand name")
    parser.add_argument("--problem", type=str, help="Custom startup problem statement")
    parser.add_argument("--solution", type=str, help="Custom startup solution statement")
    parser.add_argument("--target-users", type=str, help="Custom target users/customers")
    
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[INFO] Loaded configuration from {args.file}")
                return data.get("profile", data), data.get("idea", None)
        except Exception as e:
            print(f"[ERROR] Could not load from file {args.file}: {e}")

    default_profile = {
        "skills": "Python, React",
        "interests": "AI Education",
        "experience": "Student",
        "budget": "Low",
        "goal": "Build SaaS Startup",
    }

    # Check if custom idea passed via CLI flags
    has_custom_idea = bool(args.idea or args.startup_name or args.problem or args.solution)
    custom_idea_data = None
    if has_custom_idea:
        custom_idea_data = {
            "idea": args.idea or "",
            "startup_name": args.startup_name or "",
            "problem": args.problem or "",
            "solution": args.solution or "",
            "target_users": args.target_users or "",
        }

    if args.default or not sys.stdin.isatty():
        profile = {
            "skills": args.skills or default_profile["skills"],
            "interests": args.interests or default_profile["interests"],
            "experience": args.experience or default_profile["experience"],
            "budget": args.budget or default_profile["budget"],
            "goal": args.goal or default_profile["goal"],
        }
        return profile, custom_idea_data

    # Fully specified via CLI
    if args.skills and args.interests and args.experience and args.budget and args.goal:
        profile = {
            "skills": args.skills,
            "interests": args.interests,
            "experience": args.experience,
            "budget": args.budget,
            "goal": args.goal,
        }
        return profile, custom_idea_data

    print("\n" + "=" * 80)
    print("WELCOME TO HACKARENA 2.0 AUTONOMOUS STARTUP PIPELINE")
    print("=" * 80)
    
    # Interactive question: Do you already have a startup idea?
    has_idea_ans = input("Do you already have a startup idea you want to validate? (y/n) [n]: ").strip().lower()
    if has_idea_ans == "y":
        print("\n--- Enter Your Startup Idea ---")
        idea_text = input("Brief summary of your idea (e.g. AI expense tracker for freelancers): ").strip()
        s_name = input("Startup Name [optional]: ").strip()
        s_problem = input("Problem Statement [optional]: ").strip()
        s_solution = input("Solution [optional]: ").strip()
        s_users = input("Target Users [optional]: ").strip()
        custom_idea_data = {
            "idea": idea_text,
            "startup_name": s_name,
            "problem": s_problem,
            "solution": s_solution,
            "target_users": s_users,
        }

    print("\n--- Configure Founder Profile (press Enter to accept defaults) ---")
    skills = input(f"Skills [{default_profile['skills']}]: ").strip() or default_profile["skills"]
    interests = input(f"Interests [{default_profile['interests']}]: ").strip() or default_profile["interests"]
    experience = input(f"Experience [{default_profile['experience']}]: ").strip() or default_profile["experience"]
    budget = input(f"Budget [{default_profile['budget']}]: ").strip() or default_profile["budget"]
    goal = input(f"Goal [{default_profile['goal']}]: ").strip() or default_profile["goal"]

    profile = {
        "skills": skills,
        "interests": interests,
        "experience": experience,
        "budget": budget,
        "goal": goal,
    }
    print("\n[INFO] Using Founder Profile:\n", json.dumps(profile, indent=2))
    if custom_idea_data:
        print("\n[INFO] Using Custom Startup Idea:\n", json.dumps(custom_idea_data, indent=2))
        
    return profile, custom_idea_data


def print_section_header(title):
    print("\n" + "=" * 80)
    print(f" {title.upper()} ")
    print("=" * 80)


def format_output(data):
    """Converts data to a JSON string safe for Windows console output.
    Uses ensure_ascii=True so special chars like ₹ print as \\uXXXX instead of crashing.
    Files are always saved as proper UTF-8 separately.
    """
    if isinstance(data, (dict, list)):
        try:
            # Try rich UTF-8 output first (works if terminal supports it)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except (UnicodeEncodeError, UnicodeDecodeError):
            # Fallback: ASCII-safe output for legacy Windows terminals
            return json.dumps(data, indent=2, ensure_ascii=True)
    return str(data)


def safe_print(text):
    """Prints text to console, replacing any unencodable characters instead of crashing."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8', errors='replace'))


def main():
    user_profile, custom_idea_data = get_user_input()

    # ==========================
    # AGENT 1 OR CUSTOM IDEA RESOLUTION
    # ==========================
    if custom_idea_data:
        print_section_header("Skipping Agent 1 -> Using Custom User Startup Idea (IP)")
        print("[INFO] Formatting custom idea into structured blueprint...")
        blueprint = structure_user_idea(
            idea_text=custom_idea_data.get("idea"),
            user_profile=user_profile,
            startup_name=custom_idea_data.get("startup_name"),
            problem=custom_idea_data.get("problem"),
            solution=custom_idea_data.get("solution"),
            target_users=custom_idea_data.get("target_users"),
        )
        agent1_result = {"status": "skipped", "reason": "user_provided_custom_idea", "blueprint": blueprint}
    else:
        print_section_header("Running Agent 1: Startup Discovery & Blueprint")
        with Spinner("Agent 1 — Discovering startup ideas"):
            agent1_result = startup_discovery_agent(user_profile)
        blueprint = agent1_result.get("blueprint", {})

        if not blueprint or not isinstance(blueprint, dict):
            print("[WARN] Blueprint from Agent 1 was empty or unstructured. Attempting fallback extraction...")
            opportunities = agent1_result.get("opportunities", [])
            if opportunities and isinstance(opportunities, list) and isinstance(opportunities[0], dict):
                blueprint = opportunities[0]
            else:
                blueprint = {
                    "startup_name": "AI SaaS Startup",
                    "problem_statement": f"Solving efficiency challenges in {user_profile.get('interests', 'Tech')}",
                    "solution": f"AI-powered platform using {user_profile.get('skills', 'Python')}",
                    "target_users": "Professionals and Students",
                    "skills": user_profile.get("skills"),
                    "experience": user_profile.get("experience"),
                    "budget": user_profile.get("budget"),
                    "goal": user_profile.get("goal"),
                }

    safe_print("\nSTARTUP BLUEPRINT (STRUCTURED):")
    safe_print(format_output(blueprint))

    # ==========================
    # AGENT 2: MARKET RESEARCH & VALIDATION
    # ==========================
    print_section_header("Running Agent 2: Market Research & Validation")
    with Spinner("Agent 2 — Researching market, competitors, and validation"):
        agent2_result = market_research_agent(blueprint=blueprint)

    safe_print("\nMARKET VALIDATION (STRUCTURED):")
    safe_print(format_output(agent2_result.get("validation", {})))

    safe_print("\nINVESTOR FEEDBACK (STRUCTURED):")
    safe_print(format_output(agent2_result.get("investor_feedback", {})))

    # ==========================
    # AGENT 3: MVP PLANNER & ARCHITECTURE
    # ==========================
    print_section_header("Running Agent 3: MVP Planner & Architecture")
    with Spinner("Agent 3 — Planning MVP architecture and cost estimates"):
        agent3_result = mvp_planner_agent(startup_idea=blueprint, user_profile=user_profile)

    safe_print("\nSTARTUP ARCHITECT REPORT:")
    for key, value in agent3_result.items():
        if key == "yc_startups":
            continue
        print(f"\n--- {key.upper()} ---")
        safe_print(format_output(value))

    # ==========================
    # AGENT 4: PITCH DECK GENERATION
    # ==========================
    print_section_header("Running Agent 4: Investor Pitch Deck")
    with Spinner("Agent 4 — Generating 12-slide investor pitch deck"):
        pitch_deck = pitch_deck_agent(
            startup_context=blueprint,
            market_validation=agent2_result.get("validation", {}),
            architect_report={
                "features": agent3_result.get("features", {}),
                "tech_stack": agent3_result.get("tech_stack", {}),
                "revenue_strategy": agent3_result.get("revenue_strategy", {}),
                "success_probability": agent3_result.get("success_probability", {}),
                "costs": agent3_result.get("costs", {}),
            },
        )

    safe_print("\nINVESTOR PITCH DECK (STRUCTURED):")
    safe_print(format_output(pitch_deck))

    print_section_header("Pipeline Completed Successfully")

    # Medium Fix 3: Robust validation score extraction — probe multiple possible JSON key paths
    def extract_val_score(validation):
        if not isinstance(validation, dict):
            return None
        scores = validation.get("scores", {})
        if isinstance(scores, dict):
            for key in ["opportunity_score", "market_demand_score", "founder_market_fit_score", "scalability_score"]:
                v = scores.get(key)
                if v is not None:
                    return v
        for key in ["opportunity_score", "market_demand_score", "overall_score", "score"]:
            v = validation.get(key)
            if v is not None:
                return v
        return None

    val_score = extract_val_score(agent2_result.get("validation", {}))
    store_user_startup(blueprint, validation_score=val_score)

    # Save complete structured output to JSON files
    with open("startup_blueprint.json", "w", encoding="utf-8") as f:
        json.dump(blueprint, f, indent=4, ensure_ascii=False)
    print("[SUCCESS] Saved startup_blueprint.json")

    complete_report = {
        "user_profile": user_profile,
        "discovery_and_blueprint": agent1_result,
        "market_research": agent2_result,
        "mvp_planning": agent3_result,
        "pitch_deck": pitch_deck,
    }
    with open("pipeline_report.json", "w", encoding="utf-8") as f:
        json.dump(complete_report, f, indent=4, ensure_ascii=False)
    print("[SUCCESS] Saved full structured report to pipeline_report.json")

    # FIX 4: Export HTML pitch deck
    try:
        html_path = export_pitch_deck_html(pitch_deck, output_path="pitch_deck.html")
        print(f"[SUCCESS] Pitch deck HTML saved -> {html_path}")
    except Exception as e:
        print(f"[WARN] HTML export failed (non-fatal): {e}")


if __name__ == "__main__":
    main()