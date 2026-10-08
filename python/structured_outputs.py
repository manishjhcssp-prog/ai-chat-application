"""
Structured Responses and JSON Schema Validation Engine.
Enforces deterministic machine-readable outputs from LLMs with Pydantic
schema validation and self-healing JSON repair.
"""

import json
import re
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field, ValidationError


class CodeIssue(BaseModel):
    severity: str = Field(description="Low | Medium | High | Critical")
    description: str = Field(description="Explanation of the issue found")
    fix_suggestion: str = Field(description="Recommended solution")


class CodeReviewSchema(BaseModel):
    """Schema for automated code review audits."""
    language: str
    quality_score: int = Field(ge=0, le=100, description="Overall code quality rating from 0 to 100")
    summary: str
    issues_found: List[CodeIssue] = Field(default_factory=list)
    optimizations: List[str] = Field(default_factory=list)


class ActionStep(BaseModel):
    step_number: int
    title: str
    description: str
    estimated_minutes: int


class ActionPlanSchema(BaseModel):
    """Schema for structured step-by-step task execution."""
    goal: str
    estimated_total_time: str
    difficulty: str = Field(description="Beginner | Intermediate | Advanced")
    steps: List[ActionStep] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)


class ChatMessageAnalysis(BaseModel):
    """Schema for conversational intelligence and sentiment triage."""
    sentiment: str = Field(description="Positive | Neutral | Negative")
    intent: str = Field(description="Question | Bug Report | Feature Request | Feedback | Chit-Chat")
    urgency_rating: int = Field(ge=1, le=5, description="Urgency scale 1 to 5")
    key_topics: List[str] = Field(default_factory=list)
    recommended_action: str


class StructuredOutputParser:
    """
    Parses, cleans, and validates raw LLM output into typed Pydantic models
    or structured JSON dictionaries with automatic markdown stripping.
    """

    @staticmethod
    def extract_json_string(raw_text: str) -> str:
        """
        Extracts JSON substring by stripping markdown code fences or hunting
        for the first matching '{' and last '}'.
        """
        if not raw_text:
            return "{}"

        # 1. Check for markdown code fences ```json ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text, re.IGNORECASE)
        if fence_match:
            candidate = fence_match.group(1).strip()
            if candidate.startswith("{") or candidate.startswith("["):
                return candidate

        # 2. Extract outermost curly brace block
        first_brace = raw_text.find("{")
        last_brace = raw_text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return raw_text[first_brace : last_brace + 1].strip()

        # 3. Extract outermost square bracket block
        first_bracket = raw_text.find("[")
        last_bracket = raw_text.rfind("]")
        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            return raw_text[first_bracket : last_bracket + 1].strip()

        return raw_text.strip()

    @classmethod
    def parse_json(cls, raw_text: str) -> Dict[str, Any]:
        """Safely parses JSON string with trailing comma repair heuristics."""
        cleaned = cls.extract_json_string(raw_text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Self-healing attempt: remove trailing commas before closing braces/brackets
            fixed = re.sub(r",\s*([\]}])", r"\1", cleaned)
            try:
                return json.loads(fixed)
            except json.JSONDecodeError as err:
                raise ValueError(f"Failed to parse LLM structured output as valid JSON: {err}")

    @classmethod
    def validate_schema(
        cls,
        raw_text: str,
        schema_cls: Type[BaseModel],
    ) -> BaseModel:
        """Parses raw text and strictly validates against the supplied Pydantic schema."""
        parsed_dict = cls.parse_json(raw_text)
        try:
            return schema_cls.model_validate(parsed_dict)
        except ValidationError as val_err:
            raise ValueError(f"Output violated schema {schema_cls.__name__}: {val_err}")

    @staticmethod
    def get_system_prompt_for_schema(schema_cls: Type[BaseModel]) -> str:
        """Generates dynamic instruction instructing LLM to adhere to schema."""
        schema_json = json.dumps(schema_cls.model_json_schema(), indent=2)
        return (
            "CRITICAL INSTRUCTION: You MUST respond ONLY with valid JSON conforming strictly "
            f"to this JSON Schema. Do NOT include markdown fences, comments, or intro prose.\n"
            f"Schema:\n{schema_json}"
        )
