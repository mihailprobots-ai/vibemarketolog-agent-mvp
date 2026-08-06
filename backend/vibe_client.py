import json
import logging
import os
from typing import Any
from uuid import uuid4

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("vibe_client")

VIBE_API_BASE_URL = os.getenv("VIBE_API_BASE_URL", "https://lk.vibemarketolog.ru/api/agent")
VIBE_API_KEY = os.getenv("VIBE_API_KEY", "")
VIBE_TEXT_MODEL = os.getenv("VIBE_TEXT_MODEL", "claude-opus-5")
VIBE_MAX_TOKENS = int(os.getenv("VIBE_MAX_TOKENS", "2200"))


class VibeApiError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    if not VIBE_API_KEY:
        raise VibeApiError("VIBE_API_KEY is not configured. Add it to .env first.")

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
    except json.JSONDecodeError as exc:
        raise VibeApiError(f"Agent returned non-JSON text: {text[:500]}") from exc


async def estimate_agent_request(system: str, prompt: str) -> dict[str, Any]:
    body = {
        "type": "text",
        "model": VIBE_TEXT_MODEL,
        "system": system,
        "prompt": prompt,
        "max_tokens": VIBE_MAX_TOKENS,
        "effort": "medium",
        "thinking": False,
    }

    async with httpx.AsyncClient(timeout=40) as client:
        response = await client.post(
            f"{VIBE_API_BASE_URL}/generate/estimate?strict=true",
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
        "idempotency_key": f"marketing-analysis-{uuid4()}",
    }

    logger.info("Sending Vibe text generation request: model=%s max_tokens=%s", VIBE_TEXT_MODEL, VIBE_MAX_TOKENS)

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            f"{VIBE_API_BASE_URL}/generate?strict=true",
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
