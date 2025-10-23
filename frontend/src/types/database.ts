export interface GitHubPRMerge {
  id?: number
  pr_number: number
  title: string
  creator: string
  created_at: string
  html_url: string
  repo_owner: string
  repo_name: string
  summary: string | null
  file_path: string | null
}

export interface DBTModelChange {
  id?: number
  dbt_model_name: string
  pr_html_url: string | null
  ai_summary: string | null
  pr_created_at: string | null
  pr_creator: string | null
}
