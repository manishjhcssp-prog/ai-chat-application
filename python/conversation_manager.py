"""
Conversation and Chat History Management Engine.
Manages multi-turn state, roles (system, user, assistant), context sliding windows,
token estimation, and generation hyperparameter tuning.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import time
from .cost_manager import CostManager


@dataclass
class ChatMessage:
    """Represents a discrete turn in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: float = 0.0
    estimated_tokens: int = 0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()
        if not self.estimated_tokens:
            self.estimated_tokens = CostManager.estimate_tokens(self.content)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "estimated_tokens": self.estimated_tokens,
        }

    def to_api_format(self) -> Dict[str, str]:
        """Returns standard OpenAI/LLM chat completion format."""
        return {"role": self.role, "content": self.content}


class ConversationManager:
    """
    Manages multi-turn conversation lifecycle, context window constraints,
    and prompt optimization strategies.
    """

    def __init__(
        self,
        system_instruction: str = "You are a helpful, precise, and concise AI assistant.",
        max_context_tokens: int = 4096,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
    ):
        self.max_context_tokens = max_context_tokens
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.history: List[ChatMessage] = []

        # Initialize system instruction
        self.system_message: Optional[ChatMessage] = None
        self.set_system_instruction(system_instruction)

    def set_system_instruction(self, instruction: str) -> None:
        """Sets or replaces the active system persona / custom instructions."""
        clean = instruction.strip() if instruction else "You are a helpful AI assistant."
        self.system_message = ChatMessage(role="system", content=clean)

    def add_user_message(self, content: str) -> ChatMessage:
        """Appends a user prompt turn to history."""
        msg = ChatMessage(role="user", content=content.strip())
        self.history.append(msg)
        self.apply_sliding_window_if_needed()
        return msg

    def add_assistant_message(self, content: str) -> ChatMessage:
        """Appends an AI assistant response turn to history."""
        msg = ChatMessage(role="assistant", content=content.strip())
        self.history.append(msg)
        self.apply_sliding_window_if_needed()
        return msg

    def clear_history(self, preserve_system: bool = True) -> None:
        """Clears dialog turns while optionally preserving system instruction."""
        self.history.clear()
        if not preserve_system:
            self.system_message = None

    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """
        Compiles the full message array ready for LLM APIs (OpenAI / Gemini / Anthropic),
        ensuring system instructions lead the conversation.
        """
        payload: List[Dict[str, str]] = []
        if self.system_message:
            payload.append(self.system_message.to_api_format())
        for msg in self.history:
            payload.append(msg.to_api_format())
        return payload

    def estimate_total_tokens(self) -> int:
        """Calculates total estimated tokens across active system prompt and dialogue history."""
        total = self.system_message.estimated_tokens if self.system_message else 0
        total += sum(m.estimated_tokens for m in self.history)
        return total

    def apply_sliding_window_if_needed(self) -> int:
        """
        Ensures the conversation payload fits inside max_context_tokens.
        Preserves the system instruction at all costs, and trims oldest
        dialogue turns from the top of the history until under quota.
        Returns the number of pruned turns.
        """
        pruned_count = 0
        # Buffer space reserved for system prompt and completion
        effective_limit = max(256, self.max_context_tokens - self.max_tokens)

        while len(self.history) > 2 and self.estimate_total_tokens() > effective_limit:
            # Pop the oldest user or assistant turn
            self.history.pop(0)
            pruned_count += 1

        return pruned_count

    def update_parameters(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
    ) -> None:
        """Dynamically tunes generation hyperparameters."""
        if temperature is not None:
            self.temperature = max(0.0, min(2.0, float(temperature)))
        if max_tokens is not None:
            self.max_tokens = max(1, int(max_tokens))
        if top_p is not None:
            self.top_p = max(0.0, min(1.0, float(top_p)))

    def export_session(self) -> Dict[str, Any]:
        """Exports complete state for localStorage or file persistence."""
        return {
            "system_instruction": self.system_message.content if self.system_message else "",
            "parameters": {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "max_context_tokens": self.max_context_tokens,
            },
            "history": [m.to_dict() for m in self.history],
            "stats": {
                "message_count": len(self.history),
                "estimated_tokens": self.estimate_total_tokens(),
            },
        }

    def import_session(self, data: Dict[str, Any]) -> None:
        """Restores state from serialized JSON payload."""
        if "system_instruction" in data:
            self.set_system_instruction(data["system_instruction"])
        if "parameters" in data:
            params = data["parameters"]
            self.update_parameters(
                temperature=params.get("temperature"),
                max_tokens=params.get("max_tokens"),
                top_p=params.get("top_p"),
            )
            if "max_context_tokens" in params:
                self.max_context_tokens = params["max_context_tokens"]
        if "history" in data:
            self.history = [
                ChatMessage(
                    role=m["role"],
                    content=m["content"],
                    timestamp=m.get("timestamp", time.time()),
                    estimated_tokens=m.get("estimated_tokens", 0),
                )
                for m in data["history"]
            ]
