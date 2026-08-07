import logging
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from prompts import SYSTEM_PROMPT, build_marketing_prompt
from vibe_client import VibeApiError, estimate_agent_request, send_agent_request

logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="AI Marketing Analyst Agent",
    description="MVP integration with VibeMarketolog Agent API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=120)
    industry: str = Field(..., min_length=2, max_length=160)
    product: str = Field(..., min_length=5, max_length=1200)
    audience: str = Field(..., min_length=5, max_length=1200)
    location: str = Field(..., min_length=2, max_length=200)
    budget: str = Field(..., min_length=1, max_length=120)
    goal: Literal["получить лиды", "увеличить продажи", "протестировать оффер"]


class AnalyzeResponse(BaseModel):
    business_analysis: str
    target_audience: list[Any]
    marketing_hypotheses: list[Any]
    offer_variants: list[Any]
    creative_ideas: list[Any]
    recommended_actions: list[Any]
    vibe_meta: dict[str, Any] | None = None
    estimate: dict[str, Any] | None = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> dict[str, Any]:
    prompt = build_marketing_prompt(payload.model_dump())

    try:
        estimate = await estimate_agent_request(SYSTEM_PROMPT, prompt)
        agent_response = await send_agent_request(SYSTEM_PROMPT, prompt)
    except VibeApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    result = agent_response["result"]
    return {
        "business_analysis": result.get("business_analysis", ""),
        "target_audience": result.get("target_audience", []),
        "marketing_hypotheses": result.get("marketing_hypotheses", []),
        "offer_variants": result.get("offer_variants", []),
        "creative_ideas": result.get("creative_ideas", []),
        "recommended_actions": result.get("recommended_actions", []),
        "vibe_meta": agent_response.get("vibe_meta"),
        "estimate": estimate,
    }


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
