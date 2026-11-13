"""Normalized provider response dataclasses."""

from dataclasses import dataclass
from typing import Any
import json

from entity.messages import Message


class ProviderResponseError(RuntimeError):
    """An HTTP-success response that cannot be treated as a completed model turn."""

    def __init__(self, reason: str, detail: str = "", *, diagnostics: dict | None = None):
        self.reason = reason
        self.diagnostics = diagnostics or {}
        super().__init__(f"Provider response failed ({reason})" + (f": {detail}" if detail else ""))


def validate_tool_calls(message: Message) -> None:
    """Reject unusable calls before executing any tool in a batch."""
    seen = set()
    for call in message.tool_calls or []:
        if not call.function_name or not call.id or call.id in seen:
            raise ProviderResponseError("invalid_tool_call", "Missing name/id or duplicate tool id")
        seen.add(call.id)
        try:
            arguments = json.loads(call.arguments)
        except (ValueError, TypeError) as exc:
            raise ProviderResponseError("invalid_tool_arguments", f"tool={call.function_name}") from exc
        if not isinstance(arguments, dict):
            raise ProviderResponseError("invalid_tool_arguments", "Tool arguments must be a JSON object")


@dataclass
class ModelResponse:
    """Represents a provider response with normalized message payload."""

    message: Message
    raw_response: Any | None = None
    finish_reason: str | None = None

    def has_tool_calls(self) -> bool:
        return bool(self.message.tool_calls)

    def to_dict(self) -> dict:
        """Return a simple dict representation for compatibility."""
        payload = {
            "role": self.message.role.value,
        }
        if isinstance(self.message.content, list):
            payload["content"] = [
                block.to_dict() if hasattr(block, "to_dict") else block for block in self.message.content  # type: ignore[arg-type]
            ]
        else:
            payload["content"] = self.message.content
        if self.message.tool_calls:
            payload["tool_calls"] = [call.to_openai_dict() for call in self.message.tool_calls]
        if self.message.tool_call_id:
            payload["tool_call_id"] = self.message.tool_call_id
        if self.message.name:
            payload["name"] = self.message.name
        return payload

    def str_raw_response(self):
        return self.raw_response.__str__()
