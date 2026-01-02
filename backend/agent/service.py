"""
AI Agent service using Claude API with tool use.
"""

import json
import logging
from typing import Any

import anthropic

from django.conf import settings

from agent.tools import TOOLS, execute_tool

logger = logging.getLogger(__name__)


class AgentService:
    """Service for AI agent interactions."""

    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required")

        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"

    async def chat(self, message: str, conversation_history: list = None) -> dict:
        """
        Process a chat message and return a response.

        Args:
            message: The user's message
            conversation_history: Previous messages in the conversation

        Returns:
            Response with assistant message and any tool results
        """
        messages = conversation_history or []
        messages.append({"role": "user", "content": message})

        system_prompt = """You are a helpful assistant for Gov Watchdog, an application that helps citizens track US Congress members, their voting records, and sponsored legislation.

You have access to tools that let you:
- Search for Congress members by name, state, party, or chamber
- Get detailed information about specific members
- Look up bills sponsored or cosponsored by members
- View voting records for members

When users ask about Congress members, their voting history, or legislation, use the appropriate tools to find accurate information. Always be helpful, accurate, and non-partisan in your responses.

If you can't find information the user is looking for, explain what you searched for and suggest alternative queries they might try."""

        try:
            response = await self._run_agent_loop(messages, system_prompt)
            return {
                "response": response,
                "success": True,
            }
        except Exception as e:
            logger.exception("Agent error")
            return {
                "response": f"I encountered an error: {str(e)}",
                "success": False,
                "error": str(e),
            }

    async def _run_agent_loop(
        self, messages: list, system_prompt: str, max_iterations: int = 10
    ) -> str:
        """Run the agent loop, handling tool calls until we get a final response."""

        for iteration in range(max_iterations):
            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
            )

            # Check if we need to handle tool use
            if response.stop_reason == "tool_use":
                # Process all tool calls
                tool_results = []
                assistant_content = response.content

                for block in response.content:
                    if block.type == "tool_use":
                        logger.info(f"Executing tool: {block.name}")
                        try:
                            result = await execute_tool(block.name, block.input)
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps(result, default=str),
                                }
                            )
                        except Exception as e:
                            logger.error(f"Tool error: {e}")
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps({"error": str(e)}),
                                    "is_error": True,
                                }
                            )

                # Add assistant message and tool results to conversation
                messages.append({"role": "assistant", "content": assistant_content})
                messages.append({"role": "user", "content": tool_results})

            else:
                # Final response - extract text
                text_blocks = [
                    block.text for block in response.content if hasattr(block, "text")
                ]
                return "\n".join(text_blocks)

        return "I've reached my limit for this query. Please try rephrasing your question."
