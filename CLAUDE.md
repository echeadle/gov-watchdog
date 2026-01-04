# Gov Watchdog

## Project Description

A web application to track US elected representatives (House of Representatives and Senators), their bills, voting records, and campaign finances. Features an AI agent helper for natural language queries and a MongoDB database for data storage.

## Tech Stack

-   **Backend**: Django 5.x with Django REST Framework
-   **Frontend**: React 18 + Vite + TailwindCSS
-   **Database**: MongoDB (with Motor async driver)
-   **AI Agent**: Claude API with custom implementation
-   **Deployment**: Docker (self-hosted)

## Development Commands

```bash
# Backend
cd backend && python manage.py runserver

# Frontend
cd frontend && npm run dev

# Docker (full stack)
docker-compose up

# Run tests
cd backend && pytest
cd frontend && npm test
```

## API Keys Setup

See @.env.example for required environment variables:

-   `CONGRESS_API_KEY` - Congress.gov API key
-   `FEC_API_KEY` - FEC API key
-   `ANTHROPIC_API_KEY` - Claude API key
-   `MONGODB_URI` - MongoDB connection string

## Project Structure

```
gov-watchdog/
├── backend/              # Django REST API
│   ├── api/              # API endpoints
│   ├── members/          # Congress member models
│   ├── bills/            # Legislation models
│   ├── votes/            # Voting records
│   ├── finance/          # Campaign finance
│   └── agent/            # AI agent service
├── frontend/             # React + Vite
│   ├── src/
│   │   ├── components/   # Reusable components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   └── services/     # API clients
│   └── public/
└── docker/               # Docker configuration
```

## Code Guidelines

@.claude/rules/django.md
@.claude/rules/react.md
@.claude/rules/api-integration.md
@.claude/rules/mongodb.md
@.claude/rules/ai-agent.md

## External APIs

### Congress.gov API

-   Base URL: `https://api.congress.gov/v3`
-   Docs: https://api.congress.gov/
-   Features: Members, bills, votes, committees

### FEC API

-   Base URL: `https://api.open.fec.gov/v1`
-   Docs: https://api.open.fec.gov/developers/
-   Features: Campaign finance, contributions, expenditures

## Features (Stage 1)

1. Search representatives by name or state
2. View member profiles (bio, contact, party)
3. Browse bills authored/sponsored
4. View voting records
5. AI agent for natural language queries

## Future Features

-   Campaign finance tracking
-   User authentication
-   Alerts and notifications
-   Data export
-   Comparison tools

## Working with .claude Directory

The `.claude/` directory contains project-specific configuration, documentation, and working memory.

### Directory Structure
-   **`.claude/rules/`** - Code style guidelines (Django, React, MongoDB, API integration, AI agent)
-   **`.claude/agents/`** - Autonomous sub-agent definitions (17 agents - invoke via Task tool)
-   **`.claude/skills/`** - Domain knowledge and patterns (14 skills - invoke via Skill tool)
-   **`.claude/commands/`** - User-invocable slash commands (1 command - /check-context)
-   **`.claude/scratchpad/`** - Working memory files (context, TODO, research notes, decisions)

### Understanding Agents vs Skills vs Commands

**Agents** (`.claude/agents/`) - Autonomous workers
-   Invoked via: `Task` tool with `subagent_type` parameter
-   Purpose: Delegate complete tasks to specialized sub-processes
-   Example: `django-coder` agent writes Django models, views, serializers
-   When to use: Complex tasks requiring multiple tool calls and autonomous decision-making

**Skills** (`.claude/skills/`) - Knowledge bases
-   Invoked via: `Skill` tool with skill name
-   Purpose: Access domain-specific knowledge, patterns, code examples, API references
-   Example: `django-development` skill provides Django patterns and conventions
-   When to use: Need reference material, best practices, or API documentation during work

**Commands** (`.claude/commands/`) - User shortcuts
-   Invoked via: User types `/command-name` (e.g., `/check-context`)
-   Purpose: Quick access to common workflows or analysis tasks
-   Example: `/check-context` analyzes session health and token usage
-   When to use: User explicitly runs the command

### On First Interaction (Session Start)
1.  **Discover structure**: Use Glob to explore `.claude/scratchpad/*.md` to see what documentation exists
2.  **Read core context**: Read `context.md` for project overview and `patterns.md` for codebase conventions
3.  **Check current state**: Read `TODO.md` for active tasks and latest `session-notes.md` entry for recent work
4.  **Review existing research**: Before researching APIs or features, check if documentation already exists (e.g., `BILL-API-REFERENCE.md`)
5.  **Load relevant skills**: If working in a specific domain, invoke the relevant skill for context
    -   Working on Django backend? Invoke `django-development` skill
    -   Implementing React UI? Invoke `react-development` skill
    -   Need Congress.gov API info? Invoke `congress-data-lookup` skill
    -   This loads domain knowledge into context before you start working

### During Work
-   **Keep only decision-critical info in chat** - Offload large outputs to files, reference them with bullets
-   **After each task**: Update `TODO.md` to reflect current state (mark completed, add new tasks)
-   **When discovering something**: Append to `research-notes.md` with date/time, sources, key points, confidence level
-   **When making architectural choice**: Log in `decisions.md` with rationale, alternatives considered, and file references
-   **When blocked**: Add to `blockers.md` with clear description, remove when resolved
-   **When finding codebase pattern**: Document in `patterns.md` to avoid re-analyzing same code
-   **When creating large documentation**: Create dedicated file (e.g., `FEATURE-NAME-REFERENCE.md`) and update index files

### At Session End
-   **Summarize session**: Add entry to `session-notes.md` with what was accomplished, bugs fixed, discoveries made
-   **Clean up TODO.md**: Remove completed items, consolidate related tasks
-   **Clear resolved blockers**: Remove entries from `blockers.md` that are no longer blocking

### File Size Management (Token Budgets)
-   **context.md**: ~400 tokens (stable, rarely changes)
-   **TODO.md**: ~300 tokens (rewrite frequently, keep only active tasks)
-   **research-notes.md**: ~500 tokens (archive monthly or consolidate into dedicated docs)
-   **decisions.md**: ~500 tokens (archive quarterly)
-   **blockers.md**: ~200 tokens (keep only currently active blockers)
-   **patterns.md**: ~500 tokens (grows slowly, archive when full)
-   **session-notes.md**: ~600 tokens (keep last 3-4 sessions, archive older)

When files approach limits: Consolidate overlapping docs, archive old entries, or create dedicated reference files.

### Using Project-Specific Agents and Skills

**Agents** (autonomous workers - use Task tool):
-   **react-coder**: Frontend React components, hooks, pages
-   **django-coder**: Backend Django models, views, serializers, URLs
-   **data-fetcher**: Fetching congressional data from external APIs
-   **database-engineer**: MongoDB schema design, queries, indexes
-   **code-reviewer**: Review code quality before completion
-   **code-tester**: Write and run tests for new features
-   **debugger**: Investigate bugs and errors
-   **refactorer**: Code cleanup and optimization
-   See `.claude/agents/` for full list (17 total)

**Skills** (knowledge bases - use Skill tool):
-   **django-development**: Django/DRF patterns, models, views, serializers
-   **react-development**: React/Vite patterns, components, hooks, state management
-   **mongodb-engineering**: MongoDB schemas, queries, aggregations, indexes
-   **congress-data-lookup**: Congress.gov API reference, endpoints, data structures
-   **campaign-finance**: FEC API integration, contribution tracking
-   **bill-summarizer**: Bill analysis and summarization patterns
-   **voting-analysis**: Voting record analysis and comparison patterns
-   **member-comparison**: Side-by-side member comparison tools
-   **committee-tracking**: Congressional committee tracking
-   **ai-helper**: Claude API integration patterns
-   **docker-devops**: Docker and deployment configuration
-   **testing-qa**: Testing strategies for Django and React
-   **api-client-development**: API client wrappers and integrations
-   **claude-agent-development**: Claude API and agent development patterns
-   See `.claude/skills/` for full list (14 total)

**When to use Skills:**
-   Before implementing a feature in a domain (e.g., invoke `django-development` before building Django endpoints)
-   When you need API reference material (e.g., `congress-data-lookup` for Congress.gov endpoints)
-   To understand project conventions (e.g., `react-development` for component patterns)
-   As a knowledge boost during work (invoke skill, get context, then proceed)

### Cross-File Update Pattern
When completing a feature, update related files to maintain consistency:
1.  **Implementation** → Update code files
2.  **Documentation** → Update or create reference docs in scratchpad
3.  **TODO.md** → Mark tasks complete, add follow-up tasks
4.  **session-notes.md** → Summarize what was accomplished
5.  **decisions.md** (if applicable) → Log architectural choices made
6.  **patterns.md** (if applicable) → Document new patterns introduced

### Documentation Consolidation
When multiple scratchpad files overlap (e.g., `api-structure.md`, `api-examples.md`, `api-quick-ref.md`):
-   Consolidate into single comprehensive reference (e.g., `API-REFERENCE.md`)
-   Update index files to point to new consolidated doc
-   Mark old files as "archived" or remove them
-   This reduces token usage and prevents conflicting information

### Before Re-Researching
Always check scratchpad first to avoid duplicate research work:
-   Use Glob to find existing documentation: `.claude/scratchpad/*{topic}*.md`
-   If comprehensive docs exist (e.g., `BILL-API-REFERENCE.md`), reference them instead of re-fetching API data
-   Only create new research files when topic is genuinely new or existing docs are outdated
