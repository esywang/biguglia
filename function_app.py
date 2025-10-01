import azure.functions as func
import datetime
import json
import logging

app = func.FunctionApp()

@app.route(route="HelloWorld", auth_level=func.AuthLevel.ANONYMOUS)
def HelloWorld(req: func.HttpRequest) -> func.HttpResponse:
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
        logging.info(f'Webhook payload: {payload}')
        
        # Process the webhook data here
        # For now, just log it
        
        return func.HttpResponse("Webhook received successfully", status_code=200)
    except Exception as e:
        logging.error(f'Error processing webhook: {str(e)}')
        return func.HttpResponse("Error processing webhook", status_code=500)