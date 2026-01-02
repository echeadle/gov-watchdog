# Gov Watchdog

Track US Congress members, their voting records, and sponsored legislation.

## Features

- **Member Search**: Find Congress members by name, state, party, or chamber
- **Member Profiles**: View detailed information about representatives and senators
- **Voting Records**: Track how members vote on important legislation
- **Bill Tracking**: See bills sponsored and cosponsored by members
- **AI Assistant**: Chat with an AI agent to get answers about Congress

## Tech Stack

- **Backend**: Django 5.x + Django REST Framework
- **Frontend**: React 18 + Vite + TailwindCSS
- **Database**: MongoDB (local Docker or Atlas cloud)
- **AI**: Claude API with tool calling
- **Deployment**: Docker

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Congress.gov API key ([register here](https://api.congress.gov/sign-up))
- Anthropic API key (for AI features - [get one here](https://console.anthropic.com))

### 1. Environment Setup

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
CONGRESS_API_KEY=your-congress-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### 2. Start the Application

```bash
docker compose up
```

This starts:
- **MongoDB** at localhost:27017
- **Backend API** at http://localhost:8000
- **Frontend** at http://localhost:5173

### 3. Sync Congress Members

Populate the database with current Congress members:

```bash
./scripts/db-manage.sh sync-members
```

Or sync individual chambers:
```bash
./scripts/db-manage.sh sync-house
./scripts/db-manage.sh sync-senate
```

## Database Management

The `scripts/db-manage.sh` script provides commands for managing the local MongoDB:

| Command | Description |
|---------|-------------|
| `sync-members` | Sync all current Congress members from Congress.gov |
| `sync-house` | Sync only House members |
| `sync-senate` | Sync only Senate members |
| `stats` | Show database statistics (counts, party breakdown) |
| `shell` | Open MongoDB shell for direct queries |
| `export` | Export database to JSON files |
| `import <dir>` | Import database from JSON files |
| `reset` | Reset database (deletes all data) |

### Examples

```bash
# View database stats
./scripts/db-manage.sh stats

# Open MongoDB shell
./scripts/db-manage.sh shell

# Export data for backup
./scripts/db-manage.sh export

# Import from a previous export
./scripts/db-manage.sh import ./data/exports/20240101_120000

# Reset and start fresh
./scripts/db-manage.sh reset
```

### Direct Docker Commands

```bash
# Sync members via docker compose
docker compose exec backend python manage.py sync_members

# Access MongoDB shell directly
docker compose exec mongodb mongosh "mongodb://admin:devpassword@localhost:27017/gov_watchdog?authSource=admin"

# View backend logs
docker compose logs -f backend

# Restart just the backend
docker compose restart backend
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/members/` | List/search members |
| GET | `/api/v1/members/{id}/` | Member detail |
| GET | `/api/v1/members/{id}/bills/` | Member's bills |
| GET | `/api/v1/members/{id}/votes/` | Member's votes |
| GET | `/api/v1/bills/{id}/` | Bill detail |
| GET | `/api/v1/votes/{id}/` | Vote detail |
| POST | `/api/v1/agent/chat/` | AI chat |

### Query Parameters

**Members List** (`/api/v1/members/`):
- `q` - Search by name
- `state` - Filter by state code (e.g., CA, TX)
- `party` - Filter by party (D, R, I)
- `chamber` - Filter by chamber (house, senate)
- `page` - Page number
- `page_size` - Results per page (default: 20)

## Project Structure

```
gov-watchdog/
├── backend/
│   ├── config/          # Django settings
│   ├── members/         # Members app
│   ├── bills/           # Bills app
│   ├── votes/           # Votes app
│   ├── agent/           # AI agent app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API clients
│   │   └── types/       # TypeScript types
│   └── package.json
├── scripts/
│   ├── db-manage.sh     # Database management script
│   └── mongo-init.js    # MongoDB initialization
├── data/
│   └── exports/         # Database exports
├── docker-compose.yml
└── README.md
```

## Development

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set MongoDB URI to local or Atlas
export MONGODB_URI=mongodb://localhost:27017
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend
docker compose exec backend pytest

# Frontend
cd frontend
npm test
```

### Code Style

```bash
# Backend
docker compose exec backend black .
docker compose exec backend ruff check .

# Frontend
cd frontend
npm run lint
```

## Data Sources

- [Congress.gov API](https://api.congress.gov/) - Member, bill, and vote data
- [FEC API](https://api.open.fec.gov/) - Campaign finance data (future)

## License

MIT
