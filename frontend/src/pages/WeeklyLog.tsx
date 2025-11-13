import { format, startOfWeek, endOfWeek, parseISO } from 'date-fns'
import { ExternalLink } from 'lucide-react'
import { usePRs } from '@/hooks/usePRs'
import type { GitHubPRMerge } from '@/types/database'

interface GroupedPRs {
  [weekLabel: string]: GitHubPRMerge[]
}

export function WeeklyLog() {
  // Use TanStack Query hook without date filters
  const { data: prs = [], isLoading, error } = usePRs({})

  function groupPRsByWeek(prs: GitHubPRMerge[]): GroupedPRs {
    const grouped: GroupedPRs = {}

    prs.forEach(pr => {
      const date = parseISO(pr.created_at)
      const weekStart = startOfWeek(date, { weekStartsOn: 0 }) // Sunday
      const weekEnd = endOfWeek(date, { weekStartsOn: 0 })
      const weekLabel = `Week of ${format(weekStart, 'MMM dd')} - ${format(weekEnd, 'MMM dd, yyyy')}`

      if (!grouped[weekLabel]) {
        grouped[weekLabel] = []
      }
      grouped[weekLabel].push(pr)
    })

    return grouped
  }

  const groupedPRs = groupPRsByWeek(prs)
  const weekLabels = Object.keys(groupedPRs)

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Release Notes</h1>
        <p className="text-muted-foreground">
          Track pull request merges to main/master branches
        </p>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="text-muted-foreground">Loading PRs...</div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md">
          Error: {error instanceof Error ? error.message : 'Failed to fetch PRs'}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && prs.length === 0 && (
        <div className="text-center py-12">
          <div className="text-muted-foreground">No PRs found</div>
        </div>
      )}

      {/* Weekly PR Groups */}
      {!isLoading && !error && prs.length > 0 && (
        <div className="space-y-8">
          {weekLabels.map(weekLabel => (
            <div key={weekLabel}>
              <h2 className="text-2xl font-semibold mb-4 border-b pb-2">
                {weekLabel}
              </h2>
              <ul className="space-y-2 list-disc list-inside">
                {groupedPRs[weekLabel].map(pr => (
                  <li key={pr.id || pr.pr_number} className="flex items-start gap-2">
                    <span className="flex-1 text-sm">
                      - {pr.summary || pr.title}
                    </span>
                    <a
                      href={pr.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-sm text-primary hover:underline shrink-0"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
