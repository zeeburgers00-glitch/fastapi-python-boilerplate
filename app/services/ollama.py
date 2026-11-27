"""Multi-provider LLM adapter with transparent fallback.

Configure one or more API keys, or run Ollama locally. API free tiers and
provider availability change; this module never promises unlimited usage.
"""
import httpx
from ..config import get_settings


async def _ollama(prompt: str, system: str, s) -> str:
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            s.ollama_base_url.rstrip("/") + "/api/generate",
            json={"model": s.ollama_model, "prompt": prompt, "system": system, "stream": False},
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()


async def _openai_compatible(base_url: str, key: str, model: str,
                             prompt: str, system: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            base_url.rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ], "temperature": 0.7},
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


async def _gemini(prompt: str, system: str, s) -> str:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{s.gemini_model}:generateContent")
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            url, params={"key": s.gemini_api_key},
            json={"systemInstruction": {"parts": [{"text": system}]},
                  "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.7}},
        )
        response.raise_for_status()
        parts = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return "\n".join(p.get("text", "") for p in parts).strip()


async def generate_text(prompt: str, system: str = "") -> str:
    s = get_settings()
    providers = {
        "groq": bool(s.groq_api_key),
        "gemini": bool(s.gemini_api_key),
        "openrouter": bool(s.openrouter_api_key),
        "ollama": bool(s.ollama_base_url and s.ollama_model),
    }
    preferred = s.llm_provider.lower()
    order = ([preferred] if preferred in providers else []) if preferred != "auto" else []
    order += [name for name in ("groq", "gemini", "openrouter", "ollama") if name not in order]
    for name in order:
        if not providers[name]:
            continue
        try:
            if name == "groq":
                result = await _openai_compatible(
                    "https://api.groq.com/openai/v1", s.groq_api_key,
                    s.groq_model, prompt, system)
            elif name == "gemini":
                result = await _gemini(prompt, system, s)
            elif name == "openrouter":
                result = await _openai_compatible(
                    "https://openrouter.ai/api/v1", s.openrouter_api_key,
                    s.openrouter_model, prompt, system)
            else:
                result = await _ollama(prompt, system, s)
            if result:
                return result
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            # A provider can be rate-limited, offline, or temporarily unavailable.
            # Continue to the next configured provider instead of failing the job.
            continue
    return ""


def provider_status() -> dict:
    s = get_settings()
    return {
        "selection": s.llm_provider,
        "configured": {
            "groq": bool(s.groq_api_key),
            "gemini": bool(s.gemini_api_key),
            "openrouter": bool(s.openrouter_api_key),
            "ollama": bool(s.ollama_base_url and s.ollama_model),
        },
        "fallback_order": ["groq", "gemini", "openrouter", "ollama"],
        "note": "Cloud free tiers have changing quotas; Ollama runs locally and is limited by your hardware.",
    }
