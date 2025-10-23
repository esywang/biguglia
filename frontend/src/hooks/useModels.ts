import { useQuery } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'

export function useModels() {
  return useQuery({
    queryKey: ['models'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('dbt_model_changes')
        .select('dbt_model_name')
        .order('dbt_model_name')

      if (error) throw error

      // Get unique model names
      const modelNames = data?.map((item: { dbt_model_name: string }) => item.dbt_model_name) || []
      const uniqueModels = [...new Set(modelNames)] as string[]

      return uniqueModels
    },
  })
}
