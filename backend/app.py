"""
FastAPI Backend Application for Local Development & API Hosting.
Exposes REST endpoints for chat completions, structured outputs,
token economics, and static frontend serving.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Ensure python core package is resolvable
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.config import load_config, AppConfig
from python.conversation_manager import ConversationManager
from python.cost_manager import CostManager, MODEL_PRICING_TABLE
from python.client import UnifiedLLMClient, LLMResponse
from python.structured_outputs import (
    StructuredOutputParser,
    CodeReviewSchema,
    ActionPlanSchema,
    ChatMessageAnalysis,
)
from python.error_handler import LLMAPIError

app = FastAPI(
    title="AI Chat Application API",
    version="1.0.0",
    description="Backend API for Module 3: LLM APIs & Application Development",
)

# Enable CORS for local cross-origin development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global SDK instances
config = load_config()
cost_manager = CostManager(budget_usd=config.session_budget_usd)
llm_client = UnifiedLLMClient(config=config, cost_manager=cost_manager)


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: Optional[str] = "gpt-4o-mini"
    system_instruction: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024
    top_p: Optional[float] = 0.95
    structured_mode: Optional[bool] = False
    api_key: Optional[str] = None  # Optional user-supplied key from browser


class StructuredRequest(BaseModel):
    prompt: str
    schema_type: str = Field(default="code_review", description="code_review | action_plan | analysis")
    model: Optional[str] = "gpt-4o-mini"


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "provider": config.get_active_provider(),
        "default_model": config.default_model,
        "budget_usd": config.session_budget_usd,
    }


@app.get("/api/models")
def list_models():
    """Returns supported models and their current pricing rates."""
    models_info = []
    for name, pricing in MODEL_PRICING_TABLE.items():
        models_info.append({
            "id": name,
            "name": name,
            "prompt_price_per_m": pricing.prompt_price_per_million,
            "completion_price_per_m": pricing.completion_price_per_million,
        })
    return {"models": models_info}


@app.get("/api/cost")
def get_cost_summary():
    """Returns current financial expenditure audit."""
    return cost_manager.get_summary_report()


@app.post("/api/chat")
def handle_chat(req: ChatRequest):
    """Processes chat request with multi-turn history, custom persona, and token accounting."""
    try:
        # Prepare messages payload
        payload_messages = []
        if req.system_instruction:
            payload_messages.append({"role": "system", "content": req.system_instruction})

        # Append incoming dialog
        for m in req.messages:
            if m.get("role") != "system":
                payload_messages.append({"role": m["role"], "content": m["content"]})

        # Override API key if user provided custom key in frontend
        active_client = llm_client
        if req.api_key:
            custom_cfg = AppConfig(
                openai_api_key=req.api_key if "gpt" in (req.model or "").lower() else config.openai_api_key,
                gemini_api_key=req.api_key if "gemini" in (req.model or "").lower() else config.gemini_api_key,
                default_model=req.model or config.default_model,
            )
            active_client = UnifiedLLMClient(config=custom_cfg, cost_manager=cost_manager)

        resp: LLMResponse = active_client.call_api(
            messages=payload_messages,
            model=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            top_p=req.top_p,
        )

        return {
            "success": True,
            "content": resp.content,
            "model": resp.model,
            "prompt_tokens": resp.prompt_tokens,
            "completion_tokens": resp.completion_tokens,
            "total_tokens": resp.total_tokens,
            "cost_usd": resp.cost_usd,
            "latency_ms": resp.latency_ms,
            "finish_reason": resp.finish_reason,
            "cost_summary": cost_manager.get_summary_report(),
        }
    except LLMAPIError as ex:
        raise HTTPException(status_code=ex.status_code or 500, detail=str(ex))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Server internal error: {ex}")


@app.post("/api/structured")
def handle_structured(req: StructuredRequest):
    """Executes structured JSON schema extraction and validates against Pydantic models."""
    schema_map = {
        "code_review": CodeReviewSchema,
        "action_plan": ActionPlanSchema,
        "analysis": ChatMessageAnalysis,
    }
    target_schema = schema_map.get(req.schema_type, CodeReviewSchema)
    sys_prompt = StructuredOutputParser.get_system_prompt_for_schema(target_schema)

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": req.prompt},
    ]

    resp = llm_client.call_api(messages=messages, model=req.model)
    try:
        validated = StructuredOutputParser.validate_schema(resp.content, target_schema)
        return {
            "success": True,
            "raw_output": resp.content,
            "parsed_json": validated.model_dump(),
            "schema_type": req.schema_type,
            "tokens": resp.total_tokens,
            "cost_usd": resp.cost_usd,
        }
    except Exception as ex:
        # Return raw parsed dictionary with validation error hint
        raw_dict = StructuredOutputParser.parse_json(resp.content)
        return {
            "success": False,
            "raw_output": resp.content,
            "parsed_json": raw_dict,
            "validation_error": str(ex),
            "tokens": resp.total_tokens,
            "cost_usd": resp.cost_usd,
        }


# Mount static assets for single-command full-stack serving
public_dir = Path(__file__).parent.parent / "public"
if public_dir.exists():
    app.mount("/static", StaticFiles(directory=str(public_dir)), name="static")

    @app.get("/")
    def serve_frontend_root():
        return FileResponse(str(public_dir / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
