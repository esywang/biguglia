import { useParams, Link } from 'react-router-dom'
import { format, parseISO } from 'date-fns'
import { ExternalLink, ArrowLeft, Database } from 'lucide-react'
import { useModelChanges } from '@/hooks/useModelChanges'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export function ModelChangelog() {
  const { modelName } = useParams<{ modelName: string }>()
  const decodedModelName = modelName ? decodeURIComponent(modelName) : ''

  // Use TanStack Query hook
  const { data: changes = [], isLoading, error } = useModelChanges(decodedModelName)

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <Link to="/">
          <Button variant="ghost" className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Weekly Log
          </Button>
        </Link>

        <div className="flex items-center gap-3 mb-3">
          <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
            <Database className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-4xl font-bold">{decodedModelName}</h1>
            <p className="text-muted-foreground mt-1">dbt Model Changelog</p>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="text-muted-foreground">Loading changelog...</div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md">
          Error: {error instanceof Error ? error.message : 'Failed to fetch model changes'}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && changes.length === 0 && (
        <Card>
          <CardContent className="pt-6 text-center py-12">
            <div className="text-muted-foreground">
              No changes recorded for this model yet
            </div>
          </CardContent>
        </Card>
      )}

      {/* Timeline of Changes */}
      {!isLoading && !error && changes.length > 0 && (
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-border" />

          <div className="space-y-8">
            {changes.map((change, index) => (
              <div key={change.id || index} className="relative pl-16">
                {/* Timeline dot */}
                <div className="absolute left-4 w-5 h-5 rounded-full bg-primary border-4 border-background" />

                <Card className="hover:shadow-md transition-shadow">
                  <CardContent className="pt-6">
                    {/* Date and Creator */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        {change.pr_created_at && (
                          <span className="font-medium">
                            {format(parseISO(change.pr_created_at), 'MMM dd, yyyy')}
                          </span>
                        )}
                        {change.pr_creator && (
                          <span>
                            <strong>By:</strong> {change.pr_creator}
                          </span>
                        )}
                      </div>

                      {change.pr_html_url && (
                        <a
                          href={change.pr_html_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-sm text-primary hover:underline shrink-0"
                        >
                          View PR
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </div>

                    {/* AI Summary */}
                    {change.ai_summary ? (
                      <div className="bg-muted/50 rounded-md p-4">
                        <p className="text-sm leading-relaxed">{change.ai_summary}</p>
                      </div>
                    ) : (
                      <div className="text-sm text-muted-foreground italic">
                        No summary available for this change
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
