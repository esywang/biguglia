import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Calendar, ChevronDown, ChevronRight, Database } from 'lucide-react'
import { useModels } from '@/hooks/useModels'
import { cn } from '@/lib/utils'

export function Sidebar() {
  const [isModelsOpen, setIsModelsOpen] = useState(true)
  const location = useLocation()

  // Use TanStack Query hook
  const { data: models = [], isLoading } = useModels()

  return (
    <aside className="w-64 bg-background border-r min-h-screen flex flex-col">
      <div className="p-6 border-b">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-lg">B</span>
          </div>
          <h1 className="text-xl font-bold">Biguglia</h1>
        </div>
      </div>

      <nav className="flex-1 p-4">
        <div className="space-y-1">
          {/* Weekly PR Log */}
          <Link
            to="/"
            className={cn(
              "flex items-center space-x-3 px-3 py-2 rounded-md transition-colors",
              location.pathname === '/'
                ? "bg-primary text-primary-foreground"
                : "hover:bg-accent hover:text-accent-foreground"
            )}
          >
            <Calendar className="w-5 h-5" />
            <span className="font-medium">Weekly PR Log</span>
          </Link>

          {/* dbt Models Dropdown */}
          <div className="mt-4">
            <button
              onClick={() => setIsModelsOpen(!isModelsOpen)}
              className="flex items-center justify-between w-full px-3 py-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <div className="flex items-center space-x-3">
                <Database className="w-5 h-5" />
                <span className="font-medium">dbt Models</span>
              </div>
              {isModelsOpen ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>

            {isModelsOpen && (
              <div className="mt-1 ml-4 space-y-0.5">
                {isLoading ? (
                  <div className="px-3 py-2 text-sm text-muted-foreground">
                    Loading models...
                  </div>
                ) : models.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-muted-foreground">
                    No models found
                  </div>
                ) : (
                  models.map((model) => (
                    <Link
                      key={model}
                      to={`/model/${encodeURIComponent(model)}`}
                      className={cn(
                        "block px-3 py-2 text-sm rounded-md transition-colors truncate",
                        location.pathname === `/model/${encodeURIComponent(model)}`
                          ? "bg-primary/10 text-primary font-medium"
                          : "hover:bg-accent hover:text-accent-foreground text-muted-foreground"
                      )}
                      title={model}
                    >
                      {model}
                    </Link>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </nav>
    </aside>
  )
}
