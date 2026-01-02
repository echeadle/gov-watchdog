# Generic Claude Scratchpad Templates

Copy these files into a project at `.claude/scratchpad/`.
They are designed to stay small and be rewritten as work progresses.

**See [USAGE.md](USAGE.md) for detailed setup and usage instructions.**

## How Claude Should Use These Files

Paste the following instruction into your Claude Code prompt or `CLAUDE.md`:

```markdown
Use .claude/scratchpad as working memory.
- On first interaction: Read context.md and patterns.md for project understanding.
- Keep only decision-critical info in chat.
- Offload large outputs to files and keep only references + bullets in context.
- After each task, rewrite TODO.md to reflect current state.
- Append findings to research-notes.md with date/time, sources, key points, and confidence.
- Log architectural decisions in decisions.md with rationale and references.
- Track active blockers in blockers.md and clear resolved ones.
- Document discovered patterns in patterns.md to avoid re-analyzing code.
- Summarize sessions in session-notes.md for continuity across conversations.
- Keep each scratchpad file short and current; remove stale items.
```

## File Purpose

**User-Managed:**

- **context.md**: Project overview, tech stack, conventions (fill in once at setup)

**Claude-Managed:**

- **TODO.md**: Current tasks, rewritten frequently (~300 tokens)
- **research-notes.md**: Short research summaries with sources (~500 tokens)
- **decisions.md**: Architectural decisions with rationale (~500 tokens)
- **blockers.md**: Current blockers only (~200 tokens)
- **findings.md**: Notable findings with impact and reference (~400 tokens)
- **patterns.md**: Codebase patterns to avoid re-analyzing (~500 tokens)
- **session-notes.md**: Session summaries for continuity (~600 tokens)

**Documentation:**

- **USAGE.md**: Detailed setup and usage guide
- **README.md**: This file
- **.gitignore**: Keeps templates generic, working files private

## Quick Start

1. Copy this folder to `.claude/scratchpad/` in your project
2. Fill in `context.md` with your project details
3. Add the scratchpad instructions above to your `CLAUDE.md`
4. Let Claude manage the rest

See [USAGE.md](USAGE.md) for complete details.
