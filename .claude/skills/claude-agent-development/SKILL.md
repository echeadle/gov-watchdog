---
name: claude-agent-development
description: Claude API integration and agent development. Use when building the AI helper, implementing tool calling, or managing conversation context.
allowed-tools: Read, Write, Edit, Bash
---

# Claude Agent Development Skill

## Anthropic SDK Setup

### Installation
```bash
pip install anthropic
```

### Client Configuration
```python
# backend/agent/client.py
import anthropic
from django.conf import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

# For async operations
async_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
```

## Tool Definitions

### Define Available Tools
```python
# backend/agent/tools.py
TOOLS = [
    {
        "name": "search_members",
        "description": "Search for US Congress members by name, state, party, or chamber. Returns a list of matching members with their basic info.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Name or partial name to search for"
                },
                "state": {
                    "type": "string",
                    "description": "Two-letter state code (e.g., CA, TX, NY)"
                },
                "party": {
                    "type": "string",
                    "enum": ["D", "R", "I"],
                    "description": "Party affiliation: D=Democrat, R=Republican, I=Independent"
                },
                "chamber": {
                    "type": "string",
                    "enum": ["house", "senate"],
                    "description": "Which chamber of Congress"
                }
            }
        }
    },
    {
        "name": "get_member_details",
        "description": "Get detailed information about a specific Congress member including bio, contact info, and current term.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bioguide_id": {
                    "type": "string",
                    "description": "The member's unique bioguide identifier"
                }
            },
            "required": ["bioguide_id"]
        }
    },
    {
        "name": "get_member_bills",
        "description": "Get bills sponsored or cosponsored by a Congress member.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bioguide_id": {
                    "type": "string",
                    "description": "The member's bioguide ID"
                },
                "type": {
                    "type": "string",
                    "enum": ["sponsored", "cosponsored"],
                    "default": "sponsored"
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of bills to return"
                }
            },
            "required": ["bioguide_id"]
        }
    },
    {
        "name": "get_member_votes",
        "description": "Get the voting record for a Congress member.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bioguide_id": {
                    "type": "string",
                    "description": "The member's bioguide ID"
                },
                "congress": {
                    "type": "integer",
                    "description": "Congress number (e.g., 118 for 118th Congress)"
                },
                "limit": {
                    "type": "integer",
                    "default": 20
                }
            },
            "required": ["bioguide_id"]
        }
    },
    {
        "name": "search_bills",
        "description": "Search for bills by keyword, subject, or congress.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term for bill title or content"
                },
                "congress": {
                    "type": "integer",
                    "description": "Congress number"
                },
                "subject": {
                    "type": "string",
                    "description": "Policy subject area"
                },
                "limit": {
                    "type": "integer",
                    "default": 10
                }
            }
        }
    }
]
```

## Tool Execution

```python
# backend/agent/executor.py
import json
from members.services import MemberService
from bills.services import BillService
from votes.services import VoteService

member_service = MemberService()
bill_service = BillService()
vote_service = VoteService()

async def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return JSON result."""
    try:
        if tool_name == "search_members":
            result = await member_service.search(**tool_input)
        elif tool_name == "get_member_details":
            result = await member_service.get_by_id(tool_input["bioguide_id"])
        elif tool_name == "get_member_bills":
            result = await bill_service.get_by_sponsor(**tool_input)
        elif tool_name == "get_member_votes":
            result = await vote_service.get_by_member(**tool_input)
        elif tool_name == "search_bills":
            result = await bill_service.search(**tool_input)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return json.dumps(result, default=str)

    except Exception as e:
        return json.dumps({"error": str(e)})
```

## Agent Service

```python
# backend/agent/service.py
import anthropic
from .tools import TOOLS
from .executor import execute_tool
from django.conf import settings

SYSTEM_PROMPT = """You are Gov Watchdog's AI assistant, helping users find information about the US Congress.

You can help with:
- Finding representatives and senators by name or state
- Looking up bills and legislation they've sponsored
- Checking voting records
- Explaining how Congress works

Guidelines:
- Be accurate and cite specific data when available
- If you're not sure about something, say so
- Present information in a clear, organized way
- When listing multiple results, format them nicely
- Explain congressional terms in plain language

When presenting member information, include:
- Full name with title (Rep. or Sen.)
- Party and state (e.g., D-CA)
- Current position/term info when relevant
"""

class AgentService:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def chat(self, user_message: str, history: list = None) -> str:
        messages = (history or []) + [{"role": "user", "content": user_message}]

        while True:
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # Check if done
            if response.stop_reason == "end_turn":
                # Extract text response
                for block in response.content:
                    if hasattr(block, 'text'):
                        return block.text
                return ""

            # Handle tool use
            if response.stop_reason == "tool_use":
                # Add assistant message
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Execute tools and collect results
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                # Add tool results
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
```

## API Endpoint

```python
# backend/agent/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .service import AgentService
from .models import ConversationHistory

agent_service = AgentService()

class AgentChatView(APIView):
    async def post(self, request):
        message = request.data.get('message')
        session_id = request.data.get('session_id')

        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get conversation history
        history = await self._get_history(session_id)

        # Get response from agent
        response = await agent_service.chat(message, history)

        # Save to history
        await self._save_history(session_id, message, response)

        return Response({
            'response': response,
            'session_id': session_id
        })

    async def _get_history(self, session_id: str) -> list:
        if not session_id:
            return []

        doc = await ConversationHistory.get(session_id)
        return doc.messages[-20:] if doc else []  # Last 20 messages

    async def _save_history(self, session_id: str, user_msg: str, assistant_msg: str):
        await ConversationHistory.append(session_id, [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_msg}
        ])
```

## Conversation History Model

```python
# backend/agent/models.py
from config.database import mongodb
from datetime import datetime, timedelta

class ConversationHistory:
    collection = mongodb.db.conversations

    @classmethod
    async def get(cls, session_id: str):
        return await cls.collection.find_one({"session_id": session_id})

    @classmethod
    async def append(cls, session_id: str, messages: list):
        await cls.collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": {"$each": messages}},
                "$set": {"updated_at": datetime.utcnow()}
            },
            upsert=True
        )

    @classmethod
    async def cleanup_old(cls, max_age: timedelta = timedelta(days=1)):
        cutoff = datetime.utcnow() - max_age
        await cls.collection.delete_many({"updated_at": {"$lt": cutoff}})
```

## Error Handling

```python
# Wrap agent calls with error handling
async def safe_chat(user_message: str, history: list = None) -> str:
    try:
        return await agent_service.chat(user_message, history)
    except anthropic.RateLimitError:
        return "I'm currently experiencing high demand. Please try again in a moment."
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        return "I encountered an error processing your request. Please try again."
    except Exception as e:
        logger.exception("Unexpected error in agent")
        return "Something went wrong. Please try again."
```
