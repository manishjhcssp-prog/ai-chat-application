"""
Configuration and Environment Variable Management for LLM APIs.
Handles loading, validation, and safe retrieval of credentials and runtime parameters.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Automatically look for .env in current and parent directories
load_dotenv()


@dataclass
class AppConfig:
    """Central application configuration container with strict validations."""
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    default_temperature: float = 0.7
    default_max_tokens: int = 1024
    default_top_p: float = 0.95
    max_context_tokens: int = 4096
    session_budget_usd: float = 0.50
    enable_cost_alerts: bool = True
    debug_mode: bool = False

    def validate(self) -> None:
        """Validates configuration parameters to avoid runtime surprises."""
        if not (0.0 <= self.default_temperature <= 2.0):
            raise ValueError(f"Temperature must be in range [0.0, 2.0], got {self.default_temperature}")
        if self.default_max_tokens <= 0:
            raise ValueError(f"Max tokens must be positive, got {self.default_max_tokens}")
        if not (0.0 <= self.default_top_p <= 1.0):
            raise ValueError(f"Top-P must be in range [0.0, 1.0], got {self.default_top_p}")
        if self.max_context_tokens <= 128:
            raise ValueError(f"Max context tokens must be at least 128, got {self.max_context_tokens}")
        if self.session_budget_usd <= 0:
            raise ValueError(f"Session budget must be > 0, got {self.session_budget_usd}")

    @property
    def has_any_api_key(self) -> bool:
        """Checks if at least one real external LLM API key is present."""
        return bool(self.openai_api_key or self.gemini_api_key or self.anthropic_api_key)

    def get_active_provider(self) -> str:
        """Determines the active LLM provider based on configured keys and model choice."""
        model = self.default_model.lower()
        if "gemini" in model:
            return "gemini" if self.gemini_api_key else "simulation"
        if "claude" in model:
            return "anthropic" if self.anthropic_api_key else "simulation"
        if "gpt" in model:
            return "openai" if self.openai_api_key else "simulation"
        if self.openai_api_key:
            return "openai"
        if self.gemini_api_key:
            return "gemini"
        return "simulation"


def load_config() -> AppConfig:
    """Loads configuration from environment variables with sensible defaults."""
    config = AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        default_model=os.getenv("DEFAULT_MODEL", "gpt-4o-mini"),
        default_temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
        default_max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "1024")),
        default_top_p=float(os.getenv("DEFAULT_TOP_P", "0.95")),
        max_context_tokens=int(os.getenv("MAX_CONTEXT_TOKENS", "4096")),
        session_budget_usd=float(os.getenv("SESSION_BUDGET_USD", "0.50")),
        enable_cost_alerts=os.getenv("ENABLE_COST_ALERTS", "true").lower() in ("true", "1", "yes"),
        debug_mode=os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes"),
    )
    config.validate()
    return config
