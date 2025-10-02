import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Union, TypedDict
from dataclasses import dataclass
from datetime import datetime
from openai import OpenAI

@dataclass
class PullRequestData:
    """Data class to hold relevant PR information"""
    pr_id: int
    title: str
    description: str
    url: str
    creator: str
    created_at: str
    html_url: str

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
            if not pr:
                return None
                
            return PullRequestData(
                pr_id=pr.get('number'),
                title=pr.get('title', ''),
                description=pr.get('body') or '',  # Use empty string if body is None
                url=pr.get('url', ''),
                creator=pr.get('user', {}).get('login', ''),
                created_at=pr.get('created_at', ''),
                html_url=pr.get('html_url', '')
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
            'pr_data': None
        }
            
        # Extract PR data
        pr_data = self.extract_pr_data(payload)
        if pr_data:
            result['pr_data'] = {
                'pr_id': pr_data.pr_id,
                'title': pr_data.title,
                'creator': pr_data.creator,
                'created_at': pr_data.created_at,
                'html_url': pr_data.html_url
            }
            
            # Generate summary if OpenAI is available
            if self.openai_client:
                summary = self.generate_pr_summary(pr_data)
                if summary:
                    result['summary'] = summary
                    logging.info(f'Generated summary for PR #{pr_data.pr_id}: {summary}')
            
        # Save payload if enabled
        if self.save_payload:
            file_path = self.save_webhook_payload(payload)
            if file_path:
                result['file_path'] = file_path
                logging.info(f'Saved webhook payload to {file_path}')
                
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
