import os
import json
import re
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"


def _parse_wait_time(error_str):
    """Extracts recommended wait seconds from a Groq 429 error message."""
    try:
        match = re.search(r"(\d+)m([\d.]+)s", error_str)
        if match:
            return min(int(int(match.group(1)) * 60 + float(match.group(2))), 90)
    except Exception:
        pass
    return 0


def _call_model(model, prompt, temperature, json_mode):
    """Single attempt call to a specific model."""
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    if json_mode and "json" in prompt.lower():
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def generate(prompt, temperature=0.7, json_mode=False, retries=3):
    """
    Calls Groq LLM with:
    - Automatic exponential backoff on 429 rate limit errors (primary model).
    - Automatic fallback to llama-3.1-8b-instant if primary model exhausts all retries.
    - Returns a clean fallback JSON string if both models fail.
    """
    last_error = None

    # --- Primary model with exponential backoff ---
    for attempt in range(retries + 1):
        try:
            return _call_model(PRIMARY_MODEL, prompt, temperature, json_mode)
        except Exception as e:
            last_error = e
            error_str = str(e)
            if "429" in error_str or "rate_limit_exceeded" in error_str:
                if attempt < retries:
                    wait_hint = _parse_wait_time(error_str)
                    backoff = min(10 * (2 ** attempt), 60)
                    actual_wait = max(backoff, wait_hint)
                    print(f"[RATE LIMIT] {PRIMARY_MODEL} — attempt {attempt+1}/{retries+1}. Waiting {actual_wait}s...")
                    time.sleep(actual_wait)
                else:
                    print(f"[RATE LIMIT] {PRIMARY_MODEL} exhausted all retries. Switching to fallback model...")
            else:
                print(f"[ERROR] {PRIMARY_MODEL} non-rate-limit error: {e}")
                break

    # --- Fallback model (single attempt, no long wait) ---
    print(f"[FALLBACK] Retrying with {FALLBACK_MODEL}...")
    for attempt in range(2):
        try:
            result = _call_model(FALLBACK_MODEL, prompt, temperature, json_mode)
            print(f"[FALLBACK] {FALLBACK_MODEL} succeeded.")
            return result
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate_limit_exceeded" in error_str:
                if attempt == 0:
                    wait_hint = _parse_wait_time(error_str)
                    wait = max(15, wait_hint)
                    print(f"[FALLBACK] {FALLBACK_MODEL} also rate-limited. Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"[FALLBACK] {FALLBACK_MODEL} also exhausted. Returning fallback JSON.")
            else:
                print(f"[FALLBACK] {FALLBACK_MODEL} error: {e}")
                break

    print(f"[ERROR] Both models failed. Last error: {last_error}")
    return '{"status": "generation_failed"}'


def parse_json_from_string(text, default_fallback=None):
    if not text or not isinstance(text, str):
        return default_fallback
    text_cleaned = text.strip()
    try:
        return json.loads(text_cleaned)
    except Exception:
        pass
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text_cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception:
            pass
    dict_idx_start = text_cleaned.find("{")
    dict_idx_end = text_cleaned.rfind("}")
    list_idx_start = text_cleaned.find("[")
    list_idx_end = text_cleaned.rfind("]")
    try:
        if dict_idx_start != -1 and dict_idx_end != -1 and (list_idx_start == -1 or dict_idx_start < list_idx_start):
            return json.loads(text_cleaned[dict_idx_start : dict_idx_end + 1])
        elif list_idx_start != -1 and list_idx_end != -1:
            return json.loads(text_cleaned[list_idx_start : list_idx_end + 1])
    except Exception as e:
        print(f"[JSON] Extraction failed: {e}")
    return default_fallback


def generate_json(prompt, expected_type=dict, retries=2, default_fallback=None, temperature=0.5):
    """
    Generates structured JSON output from Groq LLM.
    Backed by exponential backoff + model fallback in generate().
    """
    if "json" not in prompt.lower():
        prompt += "\n\nIMPORTANT: You must respond with valid JSON ONLY. No markdown commentary."

    for attempt in range(retries + 1):
        try:
            use_json_mode = expected_type == dict
            content = generate(prompt, temperature=temperature, json_mode=use_json_mode)
            parsed = parse_json_from_string(content)

            if parsed is not None and isinstance(parsed, expected_type):
                return parsed

            if expected_type == dict and isinstance(parsed, list):
                if len(parsed) > 0 and isinstance(parsed[0], dict):
                    return {"items": parsed}
                return {"data": parsed}
            elif expected_type == list and isinstance(parsed, dict):
                for key in ["items", "data", "opportunities", "startups", "competitors", "features",
                            "endpoints", "pages", "weeks", "slides", "results", "tables", "ranked_opportunities"]:
                    if key in parsed and isinstance(parsed[key], list):
                        return parsed[key]
                list_vals = [v for v in parsed.values() if isinstance(v, list)]
                if len(list_vals) == 1:
                    return list_vals[0]
                return [parsed]

            print(f"[generate_json] Attempt {attempt+1}/{retries+1} — invalid type ({type(parsed).__name__}). Retrying...")
            prompt += f"\n\nERROR: Your previous output was invalid. Return ONLY a valid JSON {expected_type.__name__}."
        except Exception as e:
            print(f"[generate_json] Attempt {attempt+1} error: {e}")

    if default_fallback is not None:
        return default_fallback
    return {} if expected_type == dict else []