"""
AI Agent API views.
"""

import json
import logging
import uuid

from django.http import JsonResponse
from django.views import View

from agent.service import AgentService

logger = logging.getLogger(__name__)

# Simple in-memory conversation storage (would use Redis/DB in production)
conversations: dict[str, list] = {}


class ChatView(View):
    """
    POST /api/v1/agent/chat/
    Chat with the AI agent.
    """

    async def post(self, request):
        try:
            body = json.loads(request.body)
            message = body.get("message", "").strip()
            conversation_id = body.get("conversation_id")

            if not message:
                return JsonResponse({"error": "Message is required"}, status=400)

            # Get or create conversation
            if conversation_id and conversation_id in conversations:
                history = conversations[conversation_id]
            else:
                conversation_id = str(uuid.uuid4())
                history = []
                conversations[conversation_id] = history

            # Process message
            try:
                agent = AgentService()
                result = await agent.chat(message, history)

                # Update conversation history
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": result["response"]})

                return JsonResponse(
                    {
                        "response": result["response"],
                        "conversation_id": conversation_id,
                        "success": result.get("success", True),
                    }
                )
            except ValueError as e:
                # API key not configured
                return JsonResponse(
                    {
                        "response": "The AI assistant is not configured. Please set the ANTHROPIC_API_KEY environment variable.",
                        "conversation_id": conversation_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)
        except Exception as e:
            logger.exception("Chat error")
            return JsonResponse(
                {"error": "Internal server error", "detail": str(e)}, status=500
            )


class ConversationView(View):
    """
    GET /api/v1/agent/conversations/{id}/
    Get conversation history.

    DELETE /api/v1/agent/conversations/{id}/
    Clear conversation history.
    """

    async def get(self, request, conversation_id: str):
        if conversation_id not in conversations:
            return JsonResponse({"error": "Conversation not found"}, status=404)

        return JsonResponse(
            {
                "conversation_id": conversation_id,
                "messages": conversations[conversation_id],
            }
        )

    async def delete(self, request, conversation_id: str):
        if conversation_id in conversations:
            del conversations[conversation_id]

        return JsonResponse({"success": True})
