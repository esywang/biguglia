import azure.functions as func
import datetime
import json
import logging
import os
from pathlib import Path

app = func.FunctionApp()

def save_webhook_payload(payload: dict) -> str:
    """
    Save the webhook payload to a JSON file with timestamp in the filename.
    Returns the path to the saved file.
    """
    # Create a webhooks directory if it doesn't exist
    webhooks_dir = Path('webhooks')
    webhooks_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'webhook_payload_{timestamp}.json'
    file_path = webhooks_dir / filename
    
    # Save the payload to file
    with open(file_path, 'w') as f:
        json.dump(payload, f, indent=2)
    
    return str(file_path)

@app.route(route="HelloWorld", auth_level=func.AuthLevel.ANONYMOUS)
def hello_world(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
        
@app.route(route="github-webhook", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def github_webhook(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('GitHub webhook received')
    
    # Get the webhook payload
    try:
        payload = req.get_json()
        logging.info('Webhook payload received')
        
        # Check if this is a merge into main/master branch
        base_branch = payload.get('pull_request', {}).get('base', {}).get('ref', '')
        is_merge_to_main = (
            payload.get('action') == 'closed' and
            payload.get('pull_request', {}).get('merged') is True and
            base_branch in ['main', 'master']
        )
        
        if is_merge_to_main:
            # Save the webhook payload to file
            file_path = save_webhook_payload(payload)
            logging.info(f'Merge to {base_branch} detected - webhook payload saved to {file_path}')
            
            return func.HttpResponse(
                json.dumps({"message": "Webhook received and saved successfully", "file": file_path}),
                status_code=200,
                mimetype="application/json"
            )
        else:
            logging.info(f'Not a merge to main/master (got {base_branch}) - skipping payload save')
            return func.HttpResponse(
                json.dumps({"message": f"Webhook received but not saved (not a merge to main/master, got {base_branch})"}),
                status_code=200,
                mimetype="application/json"
            )
            
    except ValueError as e:
        logging.error(f'Error parsing webhook payload: {str(e)}')
        return func.HttpResponse("Invalid JSON payload", status_code=400)
    except Exception as e:
        logging.error(f'Error processing webhook: {str(e)}')
        return func.HttpResponse("Error processing webhook", status_code=500)