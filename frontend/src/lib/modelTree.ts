export interface TreeNode {
  name: string
  fullPath: string
  type: 'file' | 'folder'
  children?: TreeNode[]
}

export function buildModelTree(modelPaths: string[]): TreeNode[] {
  const root: TreeNode[] = []

  for (const path of modelPaths) {
    const parts = path.split('/')
    let currentLevel = root

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]
      const isFile = i === parts.length - 1
      const fullPath = parts.slice(0, i + 1).join('/')

      let existingNode = currentLevel.find((node) => node.name === part)

      if (!existingNode) {
        existingNode = {
          name: part,
          fullPath: isFile ? path : fullPath,
          type: isFile ? 'file' : 'folder',
          children: isFile ? undefined : [],
        }
        currentLevel.push(existingNode)
      }

      if (!isFile && existingNode.children) {
        currentLevel = existingNode.children
      }
    }
  }

  // Sort: folders first, then by name
  const sortTree = (nodes: TreeNode[]): TreeNode[] => {
    nodes.sort((a, b) => {
      if (a.type !== b.type) {
        return a.type === 'folder' ? -1 : 1
      }
      return a.name.localeCompare(b.name)
    })

    nodes.forEach((node) => {
      if (node.children) {
        sortTree(node.children)
      }
    })

    return nodes
  }

  return sortTree(root)
}

export function filterModelTree(tree: TreeNode[], searchQuery: string): TreeNode[] {
  if (!searchQuery.trim()) {
    return tree
  }

  const query = searchQuery.toLowerCase()

  const filterNode = (node: TreeNode): TreeNode | null => {
    // If it's a file, check if it matches
    if (node.type === 'file') {
      const matchesSearch = node.fullPath.toLowerCase().includes(query)
      return matchesSearch ? node : null
    }

    // If it's a folder, check if the folder path matches first
    if (node.children) {
      const folderPathMatches = node.fullPath.toLowerCase().includes(query)

      // If the folder path itself matches, include all children
      if (folderPathMatches) {
        return node
      }

      // Otherwise, recursively filter children
      const filteredChildren = node.children
        .map(filterNode)
        .filter((child): child is TreeNode => child !== null)

      // Include folder if it has matching children
      if (filteredChildren.length > 0) {
        return {
          ...node,
          children: filteredChildren,
        }
      }
    }

    return null
  }

  return tree
    .map(filterNode)
    .filter((node): node is TreeNode => node !== null)
}
