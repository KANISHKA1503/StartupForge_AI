import os

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = None

def get_client(api_key=None):
    global client
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        return None
    try:
        client = Groq(api_key=key)
        return client
    except Exception as e:
        print("Error initializing Groq client:", e)
        return None

# Try to initialize at startup if key is in env
get_client()

def set_api_key(api_key):
    return get_client(api_key) is not None

def generate(prompt, api_key=None):
    global client
    active_client = get_client(api_key) or client
    if not active_client:
        raise ValueError("GROQ_API_KEY is not set. Please set it in the settings panel or environment.")
    
    try:
        response = active_client.chat.completions.create(
            model="meta-llama/llama-prompt-guard-2-86m",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print("ERROR:", e)
        return """
{
    "status":"generation_failed"
}
"""