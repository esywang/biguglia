import { useState } from 'react'
import { format, startOfWeek, endOfWeek, parseISO } from 'date-fns'
import { ExternalLink, Calendar } from 'lucide-react'
import { usePRs } from '@/hooks/usePRs'
import type { GitHubPRMerge } from '@/types/database'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface GroupedPRs {
  [weekLabel: string]: GitHubPRMerge[]
}

export function WeeklyLog() {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [appliedStartDate, setAppliedStartDate] = useState('')
  const [appliedEndDate, setAppliedEndDate] = useState('')

  // Use TanStack Query hook with applied filters
  const { data: prs = [], isLoading, error } = usePRs({
    startDate: appliedStartDate,
    endDate: appliedEndDate,
  })

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

  function handleApplyFilters() {
    setAppliedStartDate(startDate)
    setAppliedEndDate(endDate)
  }

  function handleClearFilters() {
    setStartDate('')
    setEndDate('')
    setAppliedStartDate('')
    setAppliedEndDate('')
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Weekly PR Log</h1>
        <p className="text-muted-foreground">
          Track pull request merges to main/master branches across all repositories
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Filter by Date Range
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium mb-2">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium mb-2">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleApplyFilters} disabled={isLoading}>
                Apply Filters
              </Button>
              <Button variant="outline" onClick={handleClearFilters} disabled={isLoading}>
                Clear
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

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
          <div className="text-muted-foreground">No PRs found for the selected date range</div>
        </div>
      )}

      {/* Weekly PR Groups */}
      {!isLoading && !error && prs.length > 0 && (
        <div className="space-y-8">
          {weekLabels.map(weekLabel => (
            <div key={weekLabel}>
              <h2 className="text-2xl font-semibold mb-4 sticky top-0 bg-background py-2 border-b">
                {weekLabel}
              </h2>
              <div className="space-y-4">
                {groupedPRs[weekLabel].map(pr => (
                  <Card key={pr.id || pr.pr_number} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold mb-2 truncate">
                            {pr.title}
                          </h3>

                          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-3">
                            <span>
                              <strong>PR #</strong>{pr.pr_number}
                            </span>
                            <span>
                              <strong>By:</strong> {pr.creator}
                            </span>
                            <span>
                              <strong>Date:</strong> {format(parseISO(pr.created_at), 'MMM dd, yyyy')}
                            </span>
                            <span>
                              <strong>Repo:</strong> {pr.repo_owner}/{pr.repo_name}
                            </span>
                          </div>

                          {pr.summary && (
                            <div className="bg-muted/50 rounded-md p-3 mb-3">
                              <p className="text-sm leading-relaxed">{pr.summary}</p>
                            </div>
                          )}
                        </div>

                        <a
                          href={pr.html_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-sm text-primary hover:underline shrink-0"
                        >
                          View PR
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
