import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import requests
from dataclasses import dataclass
from openai import OpenAI
from supabase import create_client, Client

@dataclass
class PullRequestData:
    """Data class to hold relevant PR information"""
    pr_number: int
    title: str
    description: str
    url: str
    creator: str
    created_at: str
    html_url: str
    repo_owner: str
    repo_name: str

class WebhookProcessor:
    def __init__(self, development_mode: bool = False, save_payload: bool = False):
        """
        Initialize the webhook processor.
        
        Args:
            development_mode (bool): If True, enables local file processing mode
            save_payload (bool): If True, saves webhook payloads to file (default False)
        """
        self.development_mode = development_mode
        self.save_payload = save_payload
        self.webhooks_dir = Path('webhooks')
        self.webhooks_dir.mkdir(exist_ok=True)
        
        # Initialize OpenAI client
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            logging.warning("OPENAI_API_KEY not found in environment variables")
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        
        # Initialize Supabase client
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        if not supabase_url or not supabase_key:
            logging.warning("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
            self.supabase_client = None
        else:
            try:
                self.supabase_client: Optional[Client] = create_client(supabase_url, supabase_key)
            except Exception as e:
                logging.error(f"Failed to initialize Supabase client: {str(e)}")
                self.supabase_client = None
        
        # Initialize GitHub API client
        github_token = os.environ.get('GITHUB_TOKEN')
        if not github_token:
            logging.warning("GITHUB_TOKEN not found in environment variables")
        self.github_token = github_token
        self.github_api_base = "https://api.github.com"

    def generate_pr_summary(self, pr_data: PullRequestData) -> Optional[str]:
        """
        Generate a one-line summary of the PR using OpenAI.
        
        Args:
            pr_data (PullRequestData): The PR data to summarize
            
        Returns:
            Optional[str]: Generated summary if successful, None otherwise
        """
        if not self.openai_client:
            logging.error("OpenAI client not initialized - cannot generate summary")
            return None
            
        try:
            # Prepare the prompt
            prompt = f"""Generate a 1-2 line summary of this pull request. Focus on the main changes and impact.
            
            Title: {pr_data.title}
            Description: {pr_data.description}
            
            Respond with ONLY the summary, no additional text or formatting."""
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": "You are a technical writer who creates concise PR summaries for release notes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            # Extract and return the summary
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            return None
            
        except Exception as e:
            logging.error(f"Error generating PR summary: {str(e)}")
            return None

    def save_to_supabase(self, table_name: str, data: Union[Dict, List[Dict]]) -> bool:
        """Save data to a specified Supabase table (supports single record or batch)."""
        if not self.supabase_client:
            logging.warning("Supabase client not initialized - cannot save to database")
            return False
            
        if not data:
            logging.warning("No data provided to save to database")
            return False
            
        try:
            response = self.supabase_client.table(table_name).insert(data).execute()
            
            if response.data:
                record_count = len(response.data) if isinstance(response.data, list) else 1
                logging.info(f"Successfully saved {record_count} record(s) to {table_name} table")
                return True
            else:
                logging.error(f"Failed to save to {table_name} table - no data returned")
                return False
                
        except Exception as e:
            logging.error(f"Error saving to {table_name} table in Supabase: {str(e)}")
            return False

    def _build_pr_data_dict(self, pr_data: PullRequestData) -> Dict:
        """Build a dictionary from PullRequestData object."""
        return {
            'pr_number': pr_data.pr_number,
            'title': pr_data.title,
            'creator': pr_data.creator,
            'created_at': pr_data.created_at,
            'html_url': pr_data.html_url,
            'repo_owner': pr_data.repo_owner,
            'repo_name': pr_data.repo_name
        }
    
    def _build_dbt_model_changes_dict(self, model_filename: str, pr_data: Dict, summary: Optional[str]) -> Dict:
        """Build a dictionary for dbt model changes table."""
        return {
            'dbt_model_name': model_filename,
            'pr_html_url': pr_data.get('html_url'),
            'ai_summary': summary,
            'pr_created_at': pr_data.get('created_at'),
            'pr_creator': pr_data.get('creator'),
        }

    def _prepare_pr_merge_data(self, result_data: Dict) -> Optional[Dict]:
        """Prepare data for github_pr_merge table."""
        pr_data = result_data.get('pr_data')
        if not pr_data:
            return None
            
        return {
            **pr_data,
            'summary': result_data.get('summary'),
            'file_path': result_data.get('file_path')
        }

    def extract_pr_data(self, payload: Dict) -> Optional[PullRequestData]:
        """Extract relevant PR information from the webhook payload."""
        try:
            pr = payload.get('pull_request', {})
            repository = payload.get('repository', {})
            if not pr:
                return None
                
            return PullRequestData(
                pr_number=pr.get('number'),
                title=pr.get('title', ''),
                description=pr.get('body') or '',
                url=pr.get('url', ''),
                creator=pr.get('user', {}).get('login', ''),
                created_at=pr.get('created_at', ''),
                html_url=pr.get('html_url', ''),
                repo_owner=repository.get('owner', {}).get('login', ''),
                repo_name=repository.get('name', '')
            )
        except Exception as e:
            logging.error(f"Error extracting PR data: {str(e)}")
            return None

    def fetch_pr_files(self, repo_owner: str, repo_name: str, pr_number: int) -> Optional[List[Dict]]:
        """Fetch the list of files changed in a PR from GitHub API."""
        if not self.github_token:
            logging.error("GitHub token not available - cannot fetch PR files")
            return None
            
        try:
            url = f"{self.github_api_base}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
            headers = {
                'Authorization': f'Bearer {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            files = response.json()
            logging.info(f"Successfully fetched {len(files)} files for PR #{pr_number}")
            return files
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching PR files from GitHub API: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error fetching PR files: {str(e)}")
            return None

    def filter_sql_model_files(self, files: List[Dict]) -> List[str]:
        """Filter files to get only models/*.sql filenames."""
        sql_model_files = [
            file.get('filename', '') 
            for file in files 
            if file.get('filename', '').startswith('models/') and file.get('filename', '').endswith('.sql')
        ]
        
        if sql_model_files:
            logging.info(f"Found {len(sql_model_files)} SQL model files: {sql_model_files}")
        else:
            logging.info("No SQL model files found in this PR")
            
        return sql_model_files

    def process_webhook(self, payload: Dict) -> Optional[Dict]:
        """Process a webhook payload for PR merges to main/master branch."""
        # Check if this is a merge into main/master branch
        base_branch = payload.get('pull_request', {}).get('base', {}).get('ref', '')
        is_merge_to_main = (
            payload.get('action') == 'closed' and
            payload.get('pull_request', {}).get('merged') is True and
            base_branch in ['main', 'master']
        )
        
        if not is_merge_to_main:
            logging.info(f'Not a merge to main/master (got {base_branch}) - skipping processing')
            return None
            
        # Extract and process PR data
        pr_data = self.extract_pr_data(payload)
        if not pr_data:
            return None
            
        result = {
            'file_path': None,
            'summary': None,
            'pr_data': self._build_pr_data_dict(pr_data),
            'sql_model_files': [],
        }
        
        # Fetch and filter SQL model files
        pr_files = self.fetch_pr_files(pr_data.repo_owner, pr_data.repo_name, pr_data.pr_number)
        if pr_files:
            result['sql_model_files'] = self.filter_sql_model_files(pr_files)
        
        # Generate AI summary if available
        if self.openai_client:
            summary = self.generate_pr_summary(pr_data)
            if summary:
                result['summary'] = summary
                logging.info(f'Generated summary for PR #{pr_data.pr_number}: {summary}')
        
        # Save payload if enabled
        if self.save_payload:
            result['file_path'] = self.save_webhook_payload(payload)
        
        # Save to database
        self._save_to_database(result)
        
        return result

    def _save_to_database(self, result: Dict) -> None:
        """Save PR and model changes data to Supabase."""
        if not self.supabase_client:
            logging.info('Supabase client not available - skipping database save')
            return
            
        # Save PR merge data
        pr_merge_data = self._prepare_pr_merge_data(result)
        if pr_merge_data:
            self.save_to_supabase('github_pr_merge', pr_merge_data)

        # Save model changes in batch (more efficient than row-by-row)
        if result['sql_model_files']:
            model_changes_batch = [
                self._build_dbt_model_changes_dict(
                    sql_model_file, 
                    result['pr_data'], 
                    result.get('summary')
                )
                for sql_model_file in result['sql_model_files']
            ]
            self.save_to_supabase('dbt_model_changes', model_changes_batch)

    def save_webhook_payload(self, payload: Dict) -> str:
        """Save the webhook payload to a JSON file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'webhook_payload_{timestamp}.json'
        file_path = self.webhooks_dir / filename
        
        with open(file_path, 'w') as f:
            json.dump(payload, f, indent=2)
        
        return str(file_path)

    def process_local_file(self, file_path: Union[str, Path]) -> Optional[Dict]:
        """Process a webhook payload from a local JSON file (development mode only)."""
        if not self.development_mode:
            logging.warning("Attempted to process local file while not in development mode")
            return None
            
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path) as f:
            payload = json.load(f)
            
        return self.process_webhook(payload)
