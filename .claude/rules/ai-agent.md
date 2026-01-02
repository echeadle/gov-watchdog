---
paths: backend/agent/**/*.py, frontend/src/**/agent*.{ts,tsx}
---

# AI Agent Development Rules

## Claude API Integration

### Client Setup
```python
import anthropic

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

async def create_completion(messages, tools=None):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=messages,
        tools=tools,
    )
    return response
```

### Tool Definitions
```python
TOOLS = [
    {
        "name": "search_members",
        "description": "Search for Congress members by name or state",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Name to search"},
                "state": {"type": "string", "description": "Two-letter state code"},
            },
        },
    },
    {
        "name": "get_member_bills",
        "description": "Get bills sponsored by a specific member",
        "input_schema": {
            "type": "object",
            "properties": {
                "bioguide_id": {"type": "string", "description": "Member's bioguide ID"},
            },
            "required": ["bioguide_id"],
        },
    },
    {
        "name": "get_member_votes",
        "description": "Get voting record for a member",
        "input_schema": {
            "type": "object",
            "properties": {
                "bioguide_id": {"type": "string"},
                "congress": {"type": "integer"},
            },
            "required": ["bioguide_id"],
        },
    },
]
```

### Tool Execution
```python
async def execute_tool(tool_name: str, tool_input: dict):
    if tool_name == "search_members":
        return await member_service.search(**tool_input)
    elif tool_name == "get_member_bills":
        return await bill_service.get_by_sponsor(**tool_input)
    elif tool_name == "get_member_votes":
        return await vote_service.get_by_member(**tool_input)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
```

### Conversation Loop
```python
async def agent_conversation(user_message: str, history: list):
    messages = history + [{"role": "user", "content": user_message}]

    while True:
        response = await create_completion(messages, TOOLS)

        if response.stop_reason == "end_turn":
            return response.content[0].text

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

## System Prompt
```python
SYSTEM_PROMPT = """You are a helpful assistant for Gov Watchdog, an application that tracks US Congress members, their legislation, and voting records.

You can help users:
- Find representatives and senators by name or state
- Look up bills and legislation
- Check voting records
- Explain legislative procedures

Always be factual and cite specific data when available. If you're unsure about something, say so.

When presenting data about members:
- Include their full name, party, and state
- Mention their current term and position
- Provide relevant context about their role
"""
```

## Frontend Integration
```typescript
interface AgentMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const useAgent = () => {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (content: string) => {
    setIsLoading(true);
    try {
      const response = await agentService.chat(content, messages);
      setMessages(prev => [...prev,
        { role: 'user', content, timestamp: new Date() },
        { role: 'assistant', content: response, timestamp: new Date() },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, sendMessage, isLoading };
};
```

## Best Practices
- Keep conversation history for context
- Implement graceful error handling
- Add loading states in UI
- Log tool usage for debugging
- Validate tool inputs before execution
