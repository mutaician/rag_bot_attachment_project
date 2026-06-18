"""
Agentic RAG loop using Ollama tool calling.

Pattern: https://docs.ollama.com/capabilities/tool-calling#multi-turn-tool-calling-agent-loop
Streaming: https://docs.ollama.com/capabilities/tool-calling#tool-calling-with-streaming
"""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from app.llm.ollama_client import get_chat_client, get_chat_model
from app.rag.prompts import build_system_message
from app.rag.tools import (
    SEARCH_DOCUMENTS_TOOL,
    CitationStore,
    dispatch_tool_call,
)
from app.schemas import Citation

logger = logging.getLogger(__name__)

MAX_AGENT_ITERATIONS = 5
AGENT_TOOLS = [SEARCH_DOCUMENTS_TOOL]


@dataclass(frozen=True)
class AgentEvent:
    """Events yielded to the chat SSE layer."""

    type: str  # token | tool | citations | error
    data: dict[str, Any]


def _tool_arguments(raw: Any) -> dict:
    """Normalize Ollama tool call arguments (dict or JSON string)."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        import json

        return json.loads(raw) if raw else {}
    return {}


async def run_agent_stream(
    conversation_messages: list[dict[str, Any]],
) -> AsyncIterator[AgentEvent]:
    """
    Run the agent loop and stream the final answer.

    conversation_messages: prior turns (user/assistant), no system message.
    Yields token events during the final streaming turn, tool events during search.
    Ends with a citations event (may be empty).
    """
    client = get_chat_client()
    model = get_chat_model()
    store = CitationStore()

    messages: list[dict[str, Any]] = [
        build_system_message(),
        *conversation_messages,
    ]

    for iteration in range(MAX_AGENT_ITERATIONS):
        thinking = ""
        content = ""
        tool_calls: list[Any] = []
        pending_tokens: list[str] = []

        stream = client.chat(
            model=model,
            messages=messages,
            tools=AGENT_TOOLS,
            stream=True,
            think=True,
        )

        for chunk in stream:
            msg = chunk.message
            if msg.thinking:
                thinking += msg.thinking
            if msg.content:
                content += msg.content
                pending_tokens.append(msg.content)
            if msg.tool_calls:
                tool_calls.extend(msg.tool_calls)

        assistant_message: dict[str, Any] = {"role": "assistant", "content": content}
        if thinking:
            assistant_message["thinking"] = thinking
        if tool_calls:
            assistant_message["tool_calls"] = [
                {
                    "type": "function",
                    "function": {
                        "index": i,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for i, tc in enumerate(tool_calls)
            ]
        messages.append(assistant_message)

        if not tool_calls:
            for token in pending_tokens:
                yield AgentEvent(type="token", data={"content": token})
            break

        # Tool round — discard any streamed content from this turn.
        logger.info("Agent iteration %d: %d tool call(s)", iteration + 1, len(tool_calls))

        for call in tool_calls:
            name = call.function.name
            args = _tool_arguments(call.function.arguments)
            yield AgentEvent(
                type="tool",
                data={"name": name, "status": "running", "query": args.get("query")},
            )
            try:
                result = await dispatch_tool_call(name, args, store=store)
            except Exception as exc:
                logger.exception("Tool %s failed", name)
                result = f'{{"error": "{exc}"}}'
                yield AgentEvent(type="error", data={"message": str(exc)})

            messages.append(
                {"role": "tool", "tool_name": name, "content": result},
            )
    else:
        yield AgentEvent(
            type="error",
            data={"message": "Agent reached maximum tool iterations"},
        )

    yield AgentEvent(
        type="citations",
        data={"citations": [c.model_dump() for c in store.citations]},
    )


async def run_agent_once(user_message: str) -> tuple[str, list[Citation]]:
    """
    Non-streaming helper for tests — collects full answer + citations.
    """
    answer_parts: list[str] = []
    citations: list[Citation] = []

    async for event in run_agent_stream([{"role": "user", "content": user_message}]):
        if event.type == "token":
            answer_parts.append(event.data.get("content", ""))
        elif event.type == "citations":
            citations = [Citation(**c) for c in event.data.get("citations", [])]

    return "".join(answer_parts), citations
