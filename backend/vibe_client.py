import json
import logging
import os
from typing import Any
from uuid import uuid4

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("vibe_client")

SPA_BASE_URL = os.getenv("SPA_BASE_URL", "https://lk.vibemarketolog.ru").rstrip("/")
VIBE_API_BASE_URL = os.getenv("VIBE_API_BASE_URL", f"{SPA_BASE_URL}/api/agent")
VIBE_API_KEY = os.getenv("VIBE_API_KEY") or os.getenv("SPA_ACCESS_TOKEN", "")
VIBE_TEXT_MODEL = os.getenv("VIBE_TEXT_MODEL", "claude-opus-5")
VIBE_MAX_TOKENS = int(os.getenv("VIBE_MAX_TOKENS", "3000"))


class VibeApiError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    if not VIBE_API_KEY:
        raise VibeApiError("VIBE_API_KEY or SPA_ACCESS_TOKEN is not configured. Add it to .env first.")

    return {
        "Authorization": f"Bearer {VIBE_API_KEY}",
        "Content-Type": "application/json",
    }


def _extract_json_from_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).replace("JSON\n", "", 1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as first_error:
        try:
            return json.loads(cleaned, strict=False)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start : end + 1], strict=False)
                except json.JSONDecodeError:
                    pass
            raise VibeApiError(f"Agent returned non-JSON text: {text[:500]}") from first_error


async def estimate_agent_request(system: str, prompt: str) -> dict[str, Any]:
    body = {
        "type": "text",
        "model": VIBE_TEXT_MODEL,
        "system": system,
        "prompt": prompt,
        "max_tokens": VIBE_MAX_TOKENS,
        "effort": "medium",
        "thinking": False,
        "strict": True,
    }

    async with httpx.AsyncClient(timeout=40) as client:
        response = await client.post(
            f"{VIBE_API_BASE_URL}/generate/estimate",
            headers=_headers(),
            json=body,
        )

    if response.status_code >= 400:
        logger.warning("Vibe estimate failed: %s %s", response.status_code, response.text[:1000])
        raise VibeApiError(f"Vibe estimate failed: {response.status_code} {response.text[:500]}")

    return response.json()


async def send_agent_request(system: str, prompt: str) -> dict[str, Any]:
    body = {
        "type": "text",
        "model": VIBE_TEXT_MODEL,
        "system": system,
        "prompt": prompt,
        "max_tokens": VIBE_MAX_TOKENS,
        "effort": "medium",
        "thinking": False,
        "strict": True,
        "idempotency_key": f"marketing-analysis-{uuid4()}",
    }

    logger.info("Sending Vibe text generation request: model=%s max_tokens=%s", VIBE_TEXT_MODEL, VIBE_MAX_TOKENS)

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            f"{VIBE_API_BASE_URL}/generate",
            headers=_headers(),
            json=body,
        )

    if response.status_code >= 400:
        logger.error("Vibe generate failed: %s %s", response.status_code, response.text[:1000])
        raise VibeApiError(f"Vibe generate failed: {response.status_code} {response.text[:500]}")

    data = response.json()
    if data.get("status") != "complete" or not data.get("text"):
        raise VibeApiError(f"Unexpected Vibe response: {json.dumps(data, ensure_ascii=False)[:800]}")

    parsed_result = _extract_json_from_text(data["text"])
    return {
        "result": parsed_result,
        "raw_text": data["text"],
        "vibe_meta": {
            "generation_id": data.get("generation_id"),
            "model": data.get("model"),
            "usage": data.get("usage"),
            "cost": data.get("cost"),
            "reserved": data.get("reserved"),
            "refunded": data.get("refunded"),
            "balance_after": data.get("balance_after"),
        },
    }


