import azure.functions as func
import json
import logging
import os
from webhook_processor import WebhookProcessor

# Initialize the function app
app = func.FunctionApp()

# Initialize the webhook processor
# Set development_mode based on environment variable or default to False
development_mode = os.environ.get('DEVELOPMENT_MODE', '').lower() == 'true'
webhook_processor = WebhookProcessor(development_mode=development_mode)

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
    
    try:
        # Get the webhook payload
        payload = req.get_json()
        logging.info('Webhook payload received')
        
        # Process the webhook
        file_path = webhook_processor.process_webhook(payload)
        
        if file_path:
            return func.HttpResponse(
                json.dumps({"message": "Webhook received and saved successfully", "file": file_path}),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({"message": "Webhook received but not saved (conditions not met)"}),
                status_code=200,
                mimetype="application/json"
            )
            
    except ValueError as e:
        logging.error(f'Error parsing webhook payload: {str(e)}')
        return func.HttpResponse("Invalid JSON payload", status_code=400)
    except Exception as e:
        logging.error(f'Error processing webhook: {str(e)}')
        return func.HttpResponse("Error processing webhook", status_code=500)