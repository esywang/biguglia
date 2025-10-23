# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack application for processing GitHub webhook events, specifically tracking Pull Request merges to main/master branches. It consists of:
- **Backend**: Azure Functions (Python) that receive webhooks, process PR data, generate AI summaries via OpenAI, and store results in Supabase
- **Frontend**: React + Vite + TypeScript application with Tailwind CSS

## Architecture

### Backend (`backend/`)
The backend is an Azure Functions Python application with two main endpoints:
- `HelloWorld`: Simple test endpoint
- `github-webhook`: Main webhook processor endpoint

**Key Components:**
- `function_app.py`: Azure Functions entry point with HTTP route definitions
- `webhook_processor.py`: Core business logic with the `WebhookProcessor` class that:
  - Validates PR merge events (only processes merges to main/master)
  - Fetches changed files from GitHub API using `GITHUB_TOKEN`
  - Filters for dbt SQL model files (`models/*.sql`)
  - Generates AI summaries of PRs using OpenAI
  - Saves data to two Supabase tables: `github_pr_merge` and `dbt_model_changes`
- `webhooks/`: Directory for storing webhook payloads when `save_payload=True`

**Environment Variables (in `local.settings.json`):**
- `DEVELOPMENT_MODE`: Enable local file processing mode
- `OPENAI_API_KEY`: For AI summary generation
- `SUPABASE_URL` + `SUPABASE_KEY`: Database connection
- `GITHUB_TOKEN`: To fetch PR files from GitHub API
- `AzureWebJobsStorage`: Azure Functions storage (use `UseDevelopmentStorage=true` locally)

**Database Schema:**
- `github_pr_merge`: Stores PR metadata (number, title, creator, URL, summary, etc.)
- `dbt_model_changes`: Tracks SQL model file changes per PR (model name, PR URL, AI summary)

### Frontend (`frontend/`)
React application for visualizing dbt model changes and PR history.

**Key Features:**
- **Weekly PR Log Page** (`/`): Displays all PRs merged to main/master, grouped by week with date filters
- **Model Changelog Page** (`/model/:modelName`): Shows historical changes for a specific dbt model with timeline view

**Tech Stack:**
- React 19 + TypeScript
- Vite for build tooling
- React Router for navigation
- TanStack Query (React Query) for data fetching, caching, and state management
- Supabase JS client for database access (direct from frontend)
- Tailwind CSS v4 with shadcn/ui component pattern
- date-fns for date formatting
- lucide-react for icons

**Key Components:**
- `src/components/Sidebar.tsx`: Navigation sidebar with collapsible dbt models dropdown
- `src/components/Layout.tsx`: Root layout with sidebar
- `src/pages/WeeklyLog.tsx`: Weekly PR log with date range filtering
- `src/pages/ModelChangelog.tsx`: Timeline view of model changes
- `src/hooks/usePRs.ts`: TanStack Query hook for fetching PRs with filters
- `src/hooks/useModels.ts`: TanStack Query hook for fetching unique model names
- `src/hooks/useModelChanges.ts`: TanStack Query hook for fetching model changelog
- `src/lib/supabase.ts`: Supabase client initialization
- `src/lib/queryClient.ts`: TanStack Query client configuration
- `src/types/database.ts`: TypeScript types for Supabase tables

**Data Caching:**
- TanStack Query handles all data fetching with 5-minute stale time and 10-minute cache persistence
- Query keys: `['prs', startDate, endDate]`, `['models']`, `['model-changes', modelName]`
- Automatic background refetching and request deduplication

**Environment Variables (in `.env.local`):**
- `VITE_SUPABASE_URL`: Supabase project URL
- `VITE_SUPABASE_ANON_KEY`: Supabase anonymous/public key

## Common Commands

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment (if not already active)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Azure Functions locally
func start

# Run tests
pytest tests/test_webhook_processor.py

# Run tests with verbose output
pytest -v tests/test_webhook_processor.py
```

### Frontend Development
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

## Testing

### Backend Testing
- Tests are in `backend/tests/test_webhook_processor.py`
- Tests use pytest with fixtures
- Sample webhook payload in `backend/webhooks/webhook_payload_20251002_175804.json`
- Test in development mode with `development_mode=True` and `save_payload=False`

### VS Code Debugging
Two debug configurations available (`.vscode/launch.json`):
1. **Attach to Python Functions**: Attaches debugger to running Azure Functions (port 9091)
   - Run `func start` first, then attach
2. **Python: Debug Tests**: Runs pytest tests with debugger attached

## Development Notes

### Backend Development Mode
The `WebhookProcessor` supports two special modes:
- `development_mode=True`: Enables `process_local_file()` method to test with local JSON files
- `save_payload=True`: Saves incoming webhook payloads to `webhooks/` directory

### Working with Webhooks
- PRs must be merged to `main` or `master` branch to be processed
- Only files matching `models/*.sql` pattern are tracked as dbt model changes
- If OpenAI or Supabase clients fail to initialize, the processor logs warnings but continues
- GitHub API rate limits apply when fetching PR files

### Time Handling
All timestamps use UTC via `WebhookProcessor.get_utc_timestamp()` method.

## Deployment

Backend is deployed to Azure Functions:
- URL: `https://hotcakes-func-v2-e6c0gfh9gteehxgn.canadacentral-01.azurewebsites.net/api/`
- Webhook endpoint: `/api/github-webhook`
- Test endpoint: `/api/HelloWorld`
