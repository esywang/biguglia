import json
from pathlib import Path
import pytest
from webhook_processor import WebhookProcessor

class TestWebhookProcessor:
    @pytest.fixture
    def processor(self):
        """Create a WebhookProcessor instance for testing"""
        return WebhookProcessor(development_mode=True, save_payload=False)
        
    @pytest.fixture
    def sample_webhook_payload(self) -> dict:
        """Load sample webhook payload from JSON file"""
        webhook_file = Path("webhooks/webhook_payload_20251002_175804.json")
        with open(webhook_file) as f:
            return json.load(f)
            
    def test_process_webhook_merge_to_main(self, processor: WebhookProcessor, sample_webhook_payload):
        """Test processing a webhook payload for a merge to main"""
        # Process the webhook
        result = processor.process_webhook(sample_webhook_payload)
        
        # Verify the result structure
        assert result is not None
        assert isinstance(result, dict)
        assert 'file_path' in result
        assert 'summary' in result
        assert 'pr_data' in result
        
        # Verify file was saved
        assert result['file_path'] is not None
        assert Path(result['file_path']).exists()
        
        # Verify PR data
        assert result['pr_data'] is not None
        assert result['pr_data']['pr_number'] > 0
        assert result['pr_data']['title']
        assert result['pr_data']['creator']
        assert result['pr_data']['repo_owner']
        assert result['pr_data']['repo_name']
        
        # Clean up the saved file
        if result['file_path']:
            Path(result['file_path']).unlink()