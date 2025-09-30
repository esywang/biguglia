# Azure Function App

A simple HTTP-triggered Azure Function written in Python.

## Project Structure
- `function_app.py` - Main function code containing the HTTP trigger
- `requirements.txt` - Python dependencies
- `host.json` - Host configuration
- `local.settings.json` - Local settings (not committed to source control)

## Local Development
1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run locally:
```bash
func start
```

## Deployment
The function is deployed to Azure and can be accessed at:
https://hotcakes-func-v2-e6c0gfh9gteehxgn.canadacentral-01.azurewebsites.net/api/HelloWorld

## Testing
- GET request: `/api/HelloWorld`
- GET with parameter: `/api/HelloWorld?name=YourName`
- POST with JSON: `/api/HelloWorld` with body `{"name": "YourName"}`