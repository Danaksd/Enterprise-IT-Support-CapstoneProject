"""
Shared LLM Client
=================
Single place that configures the LLM provider and exposes two helpers
that every agent uses:

    call_llm(system_prompt, user_prompt) -> str
    extract_json(raw_text) -> dict

Keeping this in one file means switching providers/models, or fixing a
parsing edge case, only has to happen once instead of in every agent.

Currently configured for Groq, which exposes an OpenAI-compatible API,
so we reuse the `openai` SDK and just point it at Groq's base URL.
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

# Load variables from a local .env file (e.g. GROQ_API_KEY) into the
# environment. Harmless no-op if .env doesn't exist (e.g. inside Docker
# when you pass --env-file instead).
load_dotenv()

MODEL_NAME = "llama-3.3-70b-versatile"  # any current Groq-hosted model works

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Send a single-turn request to Groq's chat completions API and
    return the raw text response."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=1000,
        temperature=0,  # keep extraction/classification deterministic
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def extract_json(raw_text: str) -> dict:
    """Strip common wrappers (markdown fences, stray prose) and parse JSON.
    Raises json.JSONDecodeError if the text still isn't valid JSON."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Remove ```json ... ``` or ``` ... ``` fences
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
    # If the model added any text before/after the JSON object, isolate it.
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)
