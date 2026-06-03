"""DeepSeek API client (OpenAI-compatible)."""
import json
import re
from openai import OpenAI
from ..config import settings

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
    return _client


def chat(prompt: str, system: str = "You are a helpful assistant.", max_tokens: int = 800) -> str:
    """Send a chat request to DeepSeek and return the response text."""
    client = get_client()
    try:
        resp = client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"__ERROR__:{e}"


def chat_json(prompt: str, system: str = "You are a helpful assistant. Always reply with valid JSON only.") -> dict:
    """Send a chat request and parse JSON response."""
    raw = chat(prompt, system, max_tokens=600)
    json_str = raw.strip()
    # Try to extract JSON from markdown code blocks
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", json_str, re.DOTALL)
    if m:
        json_str = m.group(1)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"error": "json_parse_failed", "raw": raw[:200]}
