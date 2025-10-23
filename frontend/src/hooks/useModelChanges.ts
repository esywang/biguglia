import { useQuery } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'
import type { DBTModelChange } from '@/types/database'

export function useModelChanges(modelName: string) {
  return useQuery({
    queryKey: ['model-changes', modelName],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('dbt_model_changes')
        .select('*')
        .eq('dbt_model_name', modelName)
        .order('pr_created_at', { ascending: false })

      if (error) throw error

      return (data || []) as DBTModelChange[]
    },
    enabled: !!modelName, // Only run query if modelName is provided
  })
}
