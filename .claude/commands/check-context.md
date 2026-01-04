# /check-context

Evaluate current session health and determine if context offloading or sub-agent spawning is required.

## Process

1. **Analyze Behavioral Symptoms**
   - Check for "Context Rot" signs: repetitive outputs, circular reasoning, or lost instructions from CLAUDE.md.
   - Evaluate response latency: Is the model "struggling" or taking longer than usual to respond?.

2. **Assess Complexity & Token Load**
   - Estimate current tool usage: If a task has required or will require >50 tool calls, it is a candidate for a sub-agent.
   - Identify "Token-Heavy" data: Are there large logs, web search results, or raw data in the current context that should be offloaded to files?.

3. **Review Scratchpad Status**
   - Check if `TODO.md` or `research-notes.md` are becoming stale or overly long (>500 tokens).
   - Determine if architectural choices from this session have been captured in `decisions.md`.

4. **Formulate Recommendation**
   - **Scenario A (Safe):** Symptoms are low and tool count is <20. Recommendation: Continue in main session.
   - **Scenario B (Rewrite):** Symptoms are appearing but task is simple. Recommendation: Rewrite scratchpad and refresh context.
   - **Scenario C (Sub-Agent):** Task is specialized or token-heavy (>50 tools). Recommendation: Spawn a Sub-Agent to isolate context.

## Output Format

# Context Health Report

## Status Summary
- **Symptom Level:** [Low/Medium/High]
- **Estimated Load:** [Safe Zone / Approaching 128K Threshold / Critical]
- **Scratchpad State:** [Current/Stale/Bloated]

## Recommended Action
**[Action Name]**
*Rationale: [Brief explanation based on the 128K rule or tool count]*

## Next Steps
1. [Step 1, e.g., "Spawn a research sub-agent"]
2. [Step 2, e.g., "Archive session-notes.md and clear current chat"]
