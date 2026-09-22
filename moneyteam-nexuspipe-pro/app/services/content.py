"""Content generation. Offline/blocked by default; OpenAI only when explicitly enabled."""
from __future__ import annotations

from ..config import get_settings


async def generate(prompt: str) -> dict:
    s = get_settings()
    if not s.enable_openai or not s.openai_api_key:
        return {
            "status": "blocked",
            "reason": "ENABLE_OPENAI is false or OPENAI_API_KEY is not configured (offline default)",
        }
    try:
        import openai
    except ImportError:
        return {"status": "blocked", "reason": "openai package is not installed"}

    client = openai.AsyncClient(api_key=s.openai_api_key, timeout=s.provider_timeout_seconds)
    resp = await client.chat.completions.create(
        model=s.openai_model,
        messages=[{"role": "user", "content": prompt}],
    )
    return {
        "status": "success",
        "model": s.openai_model,
        "text": resp.choices[0].message.content or "",
    }
