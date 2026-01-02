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

## Use of Scratchpad folder

Use .claude/scratchpad as working memory.

-   On first interaction: Read context.md and patterns.md for project understanding.
-   Keep only decision-critical info in chat.
-   Offload large outputs to files and keep only references + bullets in context.
-   After each task, rewrite TODO.md to reflect current state.
-   Append findings to research-notes.md with date/time, sources, key points, and confidence.
-   Log architectural decisions in decisions.md with rationale and references.
-   Track active blockers in blockers.md and clear resolved ones.
-   Document discovered patterns in patterns.md to avoid re-analyzing code.
-   Summarize sessions in session-notes.md for continuity across conversations.
-   Keep each scratchpad file short and current; remove stale items.
