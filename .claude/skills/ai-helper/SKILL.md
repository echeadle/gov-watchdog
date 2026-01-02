---
name: ai-helper
description: Manages the AI agent helper for user queries. Use when implementing or debugging the conversational AI interface, tool calling, or conversation flow.
allowed-tools: Read, Write, Edit, Bash
---

# AI Helper Skill

## Purpose
This skill covers the implementation and maintenance of the AI agent helper that assists users with natural language queries about Congress members, bills, and votes.

## Architecture Overview

```
User Query → API Endpoint → Claude Agent → Tool Execution → Response
                               ↓
                        Available Tools:
                        - search_members
                        - get_member_details
                        - get_member_bills
                        - get_member_votes
                        - search_bills
                        - explain_bill
```

## Agent Implementation

### API Endpoint (Django)
```python
# backend/agent/views.py
from rest_framework.views import APIView
from rest_framework.response import Response

class AgentChatView(APIView):
    async def post(self, request):
        message = request.data.get('message')
        session_id = request.data.get('session_id')

        history = await get_conversation_history(session_id)
        response = await agent_service.chat(message, history)
        await save_conversation(session_id, message, response)

        return Response({'response': response})
```

### Agent Service
```python
# backend/agent/service.py
import anthropic
from .tools import TOOLS, execute_tool

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are Gov Watchdog's AI assistant. Help users find information about:
- US Congress members (House and Senate)
- Bills and legislation
- Voting records
- Campaign finance

Be helpful, accurate, and cite specific data when available."""

async def chat(message: str, history: list) -> str:
    messages = history + [{"role": "user", "content": message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=TOOLS,
        )

        if response.stop_reason == "end_turn":
            return response.content[0].text

        # Handle tool calls
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
```

## Tool Definitions

### search_members
```python
{
    "name": "search_members",
    "description": "Search for Congress members by name or state",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Name to search for"},
            "state": {"type": "string", "description": "Two-letter state code"},
            "chamber": {"type": "string", "enum": ["house", "senate"]},
            "party": {"type": "string", "enum": ["D", "R", "I"]},
        },
    },
}
```

### get_member_bills
```python
{
    "name": "get_member_bills",
    "description": "Get bills sponsored or cosponsored by a member",
    "input_schema": {
        "type": "object",
        "properties": {
            "bioguide_id": {"type": "string"},
            "type": {"type": "string", "enum": ["sponsored", "cosponsored"]},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["bioguide_id"],
    },
}
```

### get_member_votes
```python
{
    "name": "get_member_votes",
    "description": "Get voting record for a Congress member",
    "input_schema": {
        "type": "object",
        "properties": {
            "bioguide_id": {"type": "string"},
            "congress": {"type": "integer"},
            "limit": {"type": "integer", "default": 20},
        },
        "required": ["bioguide_id"],
    },
}
```

## Frontend Chat Component
```typescript
// frontend/src/components/AgentChat.tsx
const AgentChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await agentService.chat(input);
      setMessages(prev => [...prev, { role: 'assistant', content: response }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <MessageList messages={messages} />
      <ChatInput value={input} onChange={setInput} onSend={sendMessage} />
    </div>
  );
};
```

## Session Management
- Store conversation history in MongoDB
- Limit history to last 20 messages for context window
- Clear sessions after 24 hours of inactivity

## Error Handling
- Graceful fallback for API failures
- User-friendly error messages
- Retry logic for transient errors
