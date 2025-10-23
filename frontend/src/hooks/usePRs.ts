import { useQuery } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'
import type { GitHubPRMerge } from '@/types/database'

interface UsePRsOptions {
  startDate?: string
  endDate?: string
}

export function usePRs(options: UsePRsOptions = {}) {
  return useQuery({
    queryKey: ['prs', options.startDate, options.endDate],
    queryFn: async () => {
      let query = supabase
        .from('github_pr_merge')
        .select('*')
        .order('created_at', { ascending: false })

      if (options.startDate) {
        query = query.gte('created_at', options.startDate)
      }
      if (options.endDate) {
        query = query.lte('created_at', options.endDate)
      }

      const { data, error } = await query

      if (error) throw error

      return (data || []) as GitHubPRMerge[]
    },
  })
}
