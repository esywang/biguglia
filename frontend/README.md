# Biguglia Frontend - dbt Model Changelog Dashboard

A React application for tracking and visualizing dbt model changes from GitHub Pull Requests.

## Features

### 1. Weekly PR Log
- View all PRs merged to main/master branches
- PRs grouped by week (Sunday-Saturday)
- Date range filters to view specific time periods
- Shows PR title, creator, date, and AI-generated summary
- Direct links to GitHub PRs

### 2. dbt Model Changelog
- Sidebar lists all unique dbt models from the database
- Click any model to view its complete change history
- Timeline view showing all historical changes
- Each entry shows:
  - Date and creator of the change
  - AI-generated summary of what changed
  - Link to the PR that made the change

## Tech Stack

- **React 19** with TypeScript
- **Vite** for fast development and building
- **React Router** for navigation
- **TanStack Query (React Query)** for data fetching, caching, and state management
- **Supabase** for database access
- **Tailwind CSS v4** for styling
- **shadcn/ui** component pattern
- **date-fns** for date handling
- **lucide-react** for icons

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env.local` file with Supabase credentials:
```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

3. Run the development server:
```bash
npm run dev
```

4. Open http://localhost:5173 in your browser

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Lint code

## Database Tables

The app reads from two Supabase tables:

### `github_pr_merge`
- `pr_number` - PR number
- `title` - PR title
- `creator` - GitHub username
- `created_at` - Timestamp of PR creation
- `html_url` - Link to GitHub PR
- `repo_owner` - Repository owner
- `repo_name` - Repository name
- `summary` - AI-generated summary

### `dbt_model_changes`
- `dbt_model_name` - Name of the dbt model file (e.g., "models/marts/fact_sales.sql")
- `pr_html_url` - Link to the PR that changed this model
- `ai_summary` - AI-generated summary of the changes
- `pr_created_at` - Timestamp of the PR
- `pr_creator` - GitHub username who created the PR

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout.tsx          # Root layout with sidebar
│   │   ├── Sidebar.tsx         # Navigation sidebar
│   │   └── ui/                 # Reusable UI components
│   │       ├── button.tsx
│   │       └── card.tsx
│   ├── pages/
│   │   ├── WeeklyLog.tsx       # Weekly PR log page
│   │   └── ModelChangelog.tsx  # Model changelog page
│   ├── hooks/
│   │   ├── usePRs.ts           # TanStack Query hook for PRs
│   │   ├── useModels.ts        # TanStack Query hook for models list
│   │   └── useModelChanges.ts  # TanStack Query hook for model changes
│   ├── lib/
│   │   ├── supabase.ts         # Supabase client
│   │   ├── queryClient.ts      # TanStack Query client config
│   │   └── utils.ts            # Utility functions
│   ├── types/
│   │   └── database.ts         # TypeScript types
│   ├── App.tsx                 # Router setup
│   └── main.tsx                # Entry point with QueryClientProvider
├── .env.local                  # Environment variables (not committed)
└── package.json
```

## Usage

### Weekly PR Log
1. Navigate to the home page (/)
2. Use the date range filters to narrow down PRs
3. PRs are automatically grouped by week
4. Click "View PR" to open the PR in GitHub

### Model Changelog
1. Click on any model name in the sidebar
2. View the complete timeline of changes
3. Each entry shows when it changed, who changed it, and a summary
4. Click "View PR" to see the full PR in GitHub

## Notes

- The app connects directly to Supabase from the frontend using the anon key
- All dates are displayed in the user's local timezone
- The sidebar automatically updates when new models are added to the database
- Loading states and error messages are shown for all async operations

## Data Caching with TanStack Query

The application uses TanStack Query for efficient data management with the following benefits:

### Cache Configuration
- **Stale Time**: 5 minutes - Data is considered fresh for 5 minutes before refetching
- **GC Time**: 10 minutes - Cached data persists for 10 minutes after becoming unused
- **Retry**: Failed requests are retried once automatically
- **Refetch on Focus**: Disabled - Data doesn't automatically refetch when returning to the tab

### Query Keys
- `['prs', startDate, endDate]` - PR list query (automatically refetches when date filters change)
- `['models']` - Unique dbt model names (cached across the entire app)
- `['model-changes', modelName]` - Changes for a specific model (cached per model)

### Benefits
1. **Instant Navigation**: Clicking between models shows cached data immediately
2. **Reduced API Calls**: Same data is fetched only once within the cache window
3. **Background Updates**: Stale data is silently refetched in the background
4. **Optimistic UI**: Loading states are shown only for initial fetches
5. **Automatic Deduplication**: Multiple components requesting the same data share one request
