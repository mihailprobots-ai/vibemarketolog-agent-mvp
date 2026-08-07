import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from prompts import SYSTEM_PROMPT, build_marketing_prompt
from vibe_client import VibeApiError, estimate_agent_request, send_agent_request

ROOT_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT_DIR / "results"

load_dotenv(ROOT_DIR / ".env")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def safe_meta(response: dict[str, Any]) -> dict[str, Any]:
    return response.get("vibe_meta") or {}


def build_markdown(records: list[dict[str, Any]]) -> str:
    lines = [
        "# Live VibeMarketolog API Runs",
        "",
        "These artifacts prove that the MVP performed real requests to VibeMarketolog Agent API.",
        "The API key and webhook secret are not stored in the repository.",
        "",
        "| Run | Date UTC | Generation ID | Model | Cost | Balance after | Result file |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for index, record in enumerate(records, start=1):
        meta = safe_meta(record["response"])
        lines.append(
            "| {index} | {date} | {generation_id} | {model} | {cost} | {balance_after} | `{file}` |".format(
                index=index,
                date=record["created_at"],
                generation_id=meta.get("generation_id", "n/a"),
                model=meta.get("model", "n/a"),
                cost=meta.get("cost", "n/a"),
                balance_after=meta.get("balance_after", "n/a"),
                file=record["result_file"],
            )
        )

    lines.extend(
        [
            "",
            "## Saved fields",
            "",
            "- original business input;",
            "- generated prompt;",
            "- free cost estimate response;",
            "- generation metadata;",
            "- structured marketing analysis returned by the agent.",
            "",
        ]
    )
    return "\n".join(lines)


async def run_once(payload: dict[str, Any], run_number: int) -> dict[str, Any]:
    prompt = build_marketing_prompt(payload)
    estimate = await estimate_agent_request(SYSTEM_PROMPT, prompt)
    response = await send_agent_request(SYSTEM_PROMPT, prompt)

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    safe_stamp = created_at.replace(":", "-")
    result_file = f"live_run_{safe_stamp}_{run_number}.json"

    artifact = {
        "created_at": created_at,
        "run_number": run_number,
        "request_payload": payload,
        "system_prompt": SYSTEM_PROMPT,
        "prompt": prompt,
        "estimate": estimate,
        "response": response,
    }
    write_json(RESULTS_DIR / result_file, artifact)
    return {"created_at": created_at, "result_file": result_file, "response": response}


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run real VibeMarketolog Agent API demo calls and save artifacts.")
    parser.add_argument("--input", default=str(ROOT_DIR / "sample_request.json"), help="Path to JSON business input.")
    parser.add_argument("--repeat", type=int, default=2, help="How many real generate calls to make.")
    args = parser.parse_args()

    if not (os.getenv("VIBE_API_KEY") or os.getenv("SPA_ACCESS_TOKEN")):
        raise SystemExit("VIBE_API_KEY or SPA_ACCESS_TOKEN is not configured. Add it to .env or environment.")
    if args.repeat < 1:
        raise SystemExit("--repeat must be >= 1")

    payload = load_json(Path(args.input))
    records = []
    try:
        for run_number in range(1, args.repeat + 1):
            records.append(await run_once(payload, run_number))
    except VibeApiError as error:
        raise SystemExit(f"Vibe API error: {error}") from error

    (RESULTS_DIR / "LIVE_RUNS.md").write_text(build_markdown(records), encoding="utf-8")
    print(json.dumps({"status": "saved", "results_dir": str(RESULTS_DIR), "runs": records}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
