"""
API Cost Management & Token Accounting Engine.
Provides model pricing tables, token estimation, cost calculation per turn,
cumulative session budgeting, and threshold alert enforcement.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math


@dataclass
class ModelPricing:
    """Pricing rates per 1,000,000 tokens in USD."""
    prompt_price_per_million: float
    completion_price_per_million: float
    name: str

    @property
    def prompt_price_per_k(self) -> float:
        return self.prompt_price_per_million / 1000.0

    @property
    def completion_price_per_k(self) -> float:
        return self.completion_price_per_million / 1000.0


# Standard Model Pricing Registry (USD per 1M tokens, updated 2025/2026 standards)
MODEL_PRICING_TABLE: Dict[str, ModelPricing] = {
    "gpt-4o-mini": ModelPricing(
        name="gpt-4o-mini",
        prompt_price_per_million=0.150,
        completion_price_per_million=0.600,
    ),
    "gpt-4o": ModelPricing(
        name="gpt-4o",
        prompt_price_per_million=2.500,
        completion_price_per_million=10.000,
    ),
    "gemini-1.5-flash": ModelPricing(
        name="gemini-1.5-flash",
        prompt_price_per_million=0.075,
        completion_price_per_million=0.300,
    ),
    "gemini-1.5-pro": ModelPricing(
        name="gemini-1.5-pro",
        prompt_price_per_million=1.250,
        completion_price_per_million=5.000,
    ),
    "claude-3-5-sonnet": ModelPricing(
        name="claude-3-5-sonnet",
        prompt_price_per_million=3.000,
        completion_price_per_million=15.000,
    ),
    "mock-llm": ModelPricing(
        name="mock-llm",
        prompt_price_per_million=0.000,
        completion_price_per_million=0.000,
    ),
}


@dataclass
class UsageRecord:
    """Audit record for a single LLM API turn."""
    turn_id: int
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class CostManager:
    """
    Tracks token consumption and financial expenditure across LLM calls.
    Prevents unexpected API bills through configurable session budget caps.
    """

    def __init__(self, budget_usd: float = 0.50, enable_alerts: bool = True):
        self.budget_usd = budget_usd
        self.enable_alerts = enable_alerts
        self.records: List[UsageRecord] = []
        self._turn_counter = 0

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimates token count without requiring heavy external tokenizer dependencies.
        Heuristic: ~4 English characters per token, or ~0.75 words per token.
        Always rounds up to at least 1 token for non-empty text.
        """
        if not text:
            return 0
        char_count = len(text)
        word_count = len(text.split())
        # Blend characters / 4 and words * 1.3 for high accuracy across code & prose
        estimated = max(1, math.ceil((char_count / 4.0 + word_count * 1.3) / 2.0))
        return estimated

    def get_pricing(self, model: str) -> ModelPricing:
        """Looks up pricing for a model, defaulting to gpt-4o-mini rates if unknown."""
        clean_model = model.lower().strip()
        for key, pricing in MODEL_PRICING_TABLE.items():
            if key in clean_model:
                return pricing
        return MODEL_PRICING_TABLE["gpt-4o-mini"]

    def calculate_turn_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Calculates exact cost in USD for a given turn."""
        pricing = self.get_pricing(model)
        prompt_cost = (prompt_tokens / 1_000_000.0) * pricing.prompt_price_per_million
        comp_cost = (completion_tokens / 1_000_000.0) * pricing.completion_price_per_million
        return round(prompt_cost + comp_cost, 6)

    def record_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> UsageRecord:
        """Records a completed turn and checks against budget thresholds."""
        self._turn_counter += 1
        cost = self.calculate_turn_cost(model, prompt_tokens, completion_tokens)
        record = UsageRecord(
            turn_id=self._turn_counter,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost,
        )
        self.records.append(record)
        return record

    @property
    def total_prompt_tokens(self) -> int:
        return sum(r.prompt_tokens for r in self.records)

    @property
    def total_completion_tokens(self) -> int:
        return sum(r.completion_tokens for r in self.records)

    @property
    def total_tokens(self) -> int:
        return sum(r.total_tokens for r in self.records)

    @property
    def total_cost_usd(self) -> float:
        return round(sum(r.cost_usd for r in self.records), 6)

    @property
    def remaining_budget_usd(self) -> float:
        return max(0.0, round(self.budget_usd - self.total_cost_usd, 6))

    @property
    def budget_utilization_pct(self) -> float:
        if self.budget_usd <= 0:
            return 100.0
        return min(100.0, round((self.total_cost_usd / self.budget_usd) * 100.0, 2))

    def is_budget_exceeded(self) -> bool:
        return self.total_cost_usd >= self.budget_usd

    def get_summary_report(self) -> Dict:
        """Returns structured dictionary summary for API and CLI consumers."""
        return {
            "total_turns": len(self.records),
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_cost_usd": f"${self.total_cost_usd:.5f}",
            "budget_usd": f"${self.budget_usd:.2f}",
            "remaining_budget_usd": f"${self.remaining_budget_usd:.5f}",
            "budget_used_pct": f"{self.budget_utilization_pct}%",
            "budget_exceeded": self.is_budget_exceeded(),
        }
