import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Union, TypedDict
from dataclasses import dataclass
from datetime import datetime
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

    def save_to_supabase(self, table_name: str, data: Dict) -> bool:
        """
        Save data to a specified Supabase table.
        
        Args:
            table_name (str): Name of the Supabase table to insert into
            data (Dict): Data dictionary to insert into the table
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.supabase_client:
            logging.warning("Supabase client not initialized - cannot save to database")
            return False
            
        if not data:
            logging.warning("No data provided to save to database")
            return False
            
        try:
            # Insert into Supabase
            response = self.supabase_client.table(table_name).insert(data).execute()
            
            if response.data:
                logging.info(f"Successfully saved data to {table_name} table in Supabase")
                return True
            else:
                logging.error(f"Failed to save to {table_name} table - no data returned")
                return False
                
        except Exception as e:
            logging.error(f"Error saving to {table_name} table in Supabase: {str(e)}")
            return False

    def _build_pr_data_dict(self, pr_data: PullRequestData) -> Dict:
        """
        Build a dictionary from PullRequestData object with all PR fields.
        
        Args:
            pr_data (PullRequestData): The PR data object
            
        Returns:
            Dict: Dictionary containing all PR data fields
        """
        return {
            'pr_number': pr_data.pr_number,
            'title': pr_data.title,
            'creator': pr_data.creator,
            'created_at': pr_data.created_at,
            'html_url': pr_data.html_url,
            'repo_owner': pr_data.repo_owner,
            'repo_name': pr_data.repo_name
        }

    def prepare_pr_merge_data(self, result_data: Dict) -> Optional[Dict]:
        """
        Prepare webhook processing result data for the github_pr_merge table.
        
        Args:
            result_data (Dict): The result data from process_webhook
            
        Returns:
            Optional[Dict]: Formatted data for github_pr_merge table, None if invalid
        """
        if not result_data.get('pr_data'):
            logging.warning("No PR data available to prepare for database")
            return None
            
        try:
            # Start with the existing PR data dictionary
            insert_data = result_data['pr_data'].copy()
            
            # Add additional fields specific to github_pr_merge table
            insert_data.update({
                'summary': result_data.get('summary'),
                'file_path': result_data.get('file_path')
            })
            
            return insert_data
            
        except Exception as e:
            logging.error(f"Error preparing PR merge data: {str(e)}")
            return None

    def extract_pr_data(self, payload: Dict) -> Optional[PullRequestData]:
        """
        Extract relevant PR information from the webhook payload.
        
        Args:
            payload (Dict): The webhook payload to process
            
        Returns:
            Optional[PullRequestData]: Extracted PR data if available, None otherwise
        """
        try:
            pr = payload.get('pull_request', {})
            repository = payload.get('repository', {})
            if not pr:
                return None
                
            return PullRequestData(
                pr_number=pr.get('number'),
                title=pr.get('title', ''),
                description=pr.get('body') or '',  # Use empty string if body is None
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

    def process_webhook(self, payload: Dict) -> Optional[Dict]:
        """
        Process a webhook payload, generate summary if it's a merge to main/master,
        and optionally save the payload.
        
        Args:
            payload (Dict): The webhook payload to process
            
        Returns:
            Optional[Dict]: Processing results including file path and summary if applicable,
                          None if conditions not met
        """
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
            
        result = {
            'file_path': None,
            'summary': None,
            'pr_data': None,
            'saved_to_database': False
        }
            
        # Extract PR data
        pr_data = self.extract_pr_data(payload)
        if pr_data:
            result['pr_data'] = self._build_pr_data_dict(pr_data)
            
            # Generate summary if OpenAI is available
            if self.openai_client:
                summary = self.generate_pr_summary(pr_data)
                if summary:
                    result['summary'] = summary
                    logging.info(f'Generated summary for PR #{pr_data.pr_number}: {summary}')
            
        # Save payload if enabled
        if self.save_payload:
            file_path = self.save_webhook_payload(payload)
            if file_path:
                result['file_path'] = file_path
                logging.info(f'Saved webhook payload to {file_path}')
        
        # Save to Supabase database
        if self.supabase_client:
            # Prepare data for github_pr_merge table
            pr_merge_data = self.prepare_pr_merge_data(result)
            if pr_merge_data:
                saved_to_db = self.save_to_supabase('github_pr_merge', pr_merge_data)
                result['saved_to_database'] = saved_to_db
            else:
                result['saved_to_database'] = False
        else:
            logging.info('Supabase client not available - skipping database save')
                
        return result

    def save_webhook_payload(self, payload: Dict) -> str:
        """
        Save the webhook payload to a JSON file.
        
        Args:
            payload (Dict): The webhook payload to save
            
        Returns:
            str: Path to the saved file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'webhook_payload_{timestamp}.json'
        file_path = self.webhooks_dir / filename
        
        with open(file_path, 'w') as f:
            json.dump(payload, f, indent=2)
        
        return str(file_path)

    def process_local_file(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Process a webhook payload from a local JSON file.
        
        Args:
            file_path (Union[str, Path]): Path to the JSON file to process
            
        Returns:
            Optional[str]: Path to saved file if saved, None otherwise
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        if not self.development_mode:
            logging.warning("Attempted to process local file while not in development mode")
            return None
            
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path) as f:
            payload = json.load(f)
            
        return self.process_webhook(payload)
