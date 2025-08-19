# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Frontend Development

```bash
# Install dependencies
npm install

# Start development server (with hot reload)
npm run dev          # Default port 5173
npm run dev:5050     # Port 5050

# Build for production
npm run build

# Run type checking
npm run check

# Lint frontend code
npm run lint:frontend

# Format code
npm run format

# Run Cypress E2E tests
npm run cy:open

# Run unit tests
npm run test:frontend
```

### Backend Development

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or: brew install uv

# Install Python dependencies (requires Python 3.11-3.12)
uv pip install -r backend/requirements.txt

# Start backend server
cd backend
uv run python -m open_webui.main

# Or use the start script
./backend/start.sh

# Format Python code
npm run format:backend

# Lint Python code
npm run lint:backend
```

### Database Operations

```bash
# Run Alembic migrations
cd backend
uv run alembic upgrade head

# Create a new migration
uv run alembic revision --autogenerate -m "description"
```

### Full Stack Development

```bash
# Run both frontend and backend
npm run lint          # Lint everything
npm run format        # Format all code
```

## Architecture Overview

### Full Stack Structure

Open WebUI is a **FastAPI + SvelteKit** application with real-time capabilities via Socket.IO. The architecture separates frontend and backend cleanly while providing a unified development experience.

### Backend (`/backend/open_webui/`)

- **Entry Point**: `main.py` - FastAPI application with comprehensive middleware setup
- **API Structure**: RESTful APIs organized by domain under `/api/v1/`
- **Database**: SQLAlchemy ORM with Alembic migrations, supports SQLite/PostgreSQL/MySQL
- **Real-time**: Socket.IO integration for chat and notifications
- **Extensibility**: Plugin system via Functions, Tools, and Pipelines

#### Key Backend Patterns

- **Repository Pattern**: Each model has dedicated CRUD operations
- **Dependency Injection**: FastAPI's DI for auth and database sessions
- **Event-Driven**: Socket.IO events for real-time updates
- **Configuration**: Environment variables + database-persisted config

### Frontend (`/src/`)

- **Framework**: SvelteKit with TypeScript
- **Routing**: File-based routing under `src/routes/`
- **State Management**: Svelte stores in `src/lib/stores/`
- **API Client**: Structured API layer in `src/lib/apis/`
- **Components**: Modular components in `src/lib/components/`

#### Key Frontend Patterns

- **Layout Hierarchy**: Nested layouts for consistent UI structure
- **Type Safety**: TypeScript interfaces for all API interactions
- **Reactive State**: Svelte stores for global state management
- **Progressive Enhancement**: PWA support with offline capabilities

### Data Flow

1. **User Interaction** → SvelteKit Route → API Client (`/lib/apis/`)
2. **API Request** → FastAPI Router → Service/Repository → Database
3. **Real-time Updates** → Socket.IO Events → Store Updates → UI Reactivity

### Key Integration Points

- **Authentication**: JWT-based with FastAPI middleware and SvelteKit guards
- **File Uploads**: Multipart handling with configurable storage backends
- **RAG System**: Vector database integration for knowledge retrieval
- **Model Providers**: Unified interface for Ollama, OpenAI, and custom providers

### Extension Points

- **Functions** (`/workspace/functions/`): Python code execution in sandboxed environment
- **Tools** (`/workspace/tools/`): External tool integrations
- **Pipelines**: Custom processing pipelines for request/response transformation
- **Models**: Custom model configurations and providers

## Important Conventions

### API Endpoints

- All API routes are prefixed with `/api/v1/`
- Authentication required for most endpoints (Bearer token)
- Consistent error response format with status codes

### Database Migrations

- Use Alembic for schema changes
- Legacy Peewee migrations exist but are being phased out
- Always test migrations on a copy of production data

### Frontend Routes

- Protected routes check authentication in `+layout.js`
- Dynamic routes use `[param]` syntax
- API data fetching happens in `+page.js` or components

### Configuration

- Environment variables for deployment config
- Database-stored config for runtime settings
- Feature flags controlled via admin interface

### Testing

- Frontend: Cypress for E2E, Vitest for unit tests
- Backend: Pytest for Python tests
- Test files follow `*.test.ts` or `*.cy.ts` patterns
