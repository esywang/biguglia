import { useState, useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Calendar, ChevronDown, ChevronRight, Database, Search, Folder, File, LogOut, User } from 'lucide-react'
import { useModels } from '@/hooks/useModels'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'
import { buildModelTree, filterModelTree, type TreeNode } from '@/lib/modelTree'
import { Button } from '@/components/ui/button'

// Recursive tree node component
function TreeNodeComponent({
  node,
  depth = 0
}: {
  node: TreeNode
  depth?: number
}) {
  const [isOpen, setIsOpen] = useState(true)
  const location = useLocation()

  if (node.type === 'file') {
    return (
      <Link
        to={`/model/${encodeURIComponent(node.fullPath)}`}
        className={cn(
          "flex items-center space-x-2 px-3 py-1.5 text-sm rounded-md transition-colors truncate",
          location.pathname === `/model/${encodeURIComponent(node.fullPath)}`
            ? "bg-primary/10 text-primary font-medium"
            : "hover:bg-accent hover:text-accent-foreground text-muted-foreground"
        )}
        style={{ paddingLeft: `${depth * 12 + 12}px` }}
        title={node.fullPath}
      >
        <File className="w-4 h-4 flex-shrink-0" />
        <span className="truncate">{node.name}</span>
      </Link>
    )
  }

  return (
    <div>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 w-full px-3 py-1.5 text-sm rounded-md hover:bg-accent hover:text-accent-foreground transition-colors text-muted-foreground"
        style={{ paddingLeft: `${depth * 12 + 12}px` }}
      >
        {isOpen ? (
          <ChevronDown className="w-4 h-4 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-4 h-4 flex-shrink-0" />
        )}
        <Folder className="w-4 h-4 flex-shrink-0" />
        <span className="truncate">{node.name}</span>
      </button>
      {isOpen && node.children && (
        <div>
          {node.children.map((child) => (
            <TreeNodeComponent key={child.fullPath} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

export function Sidebar() {
  const [isModelsOpen, setIsModelsOpen] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const location = useLocation()
  const { user, signOut } = useAuth()

  // Use TanStack Query hook
  const { data: models = [], isLoading } = useModels()

  // Build tree structure and filter based on search
  const modelTree = useMemo(() => {
    const tree = buildModelTree(models)
    return filterModelTree(tree, searchQuery)
  }, [models, searchQuery])

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
              <div className="mt-2 space-y-2">
                {/* Search Input */}
                <div className="px-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder="Search models..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-3 py-1.5 text-sm bg-accent/50 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 placeholder:text-muted-foreground"
                    />
                  </div>
                </div>

                {/* Tree View */}
                <div className="max-h-[calc(100vh-300px)] overflow-y-auto">
                  {isLoading ? (
                    <div className="px-3 py-2 text-sm text-muted-foreground">
                      Loading models...
                    </div>
                  ) : modelTree.length === 0 ? (
                    <div className="px-3 py-2 text-sm text-muted-foreground">
                      {searchQuery ? 'No models match your search' : 'No models found'}
                    </div>
                  ) : (
                    <div className="space-y-0.5">
                      {modelTree.map((node) => (
                        <TreeNodeComponent key={node.fullPath} node={node} depth={0} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* User section at bottom */}
      <div className="p-4 border-t">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 min-w-0">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-primary" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium truncate">{user?.email}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={signOut}
            className="flex-shrink-0"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </aside>
  )
}
