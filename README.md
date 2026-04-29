## App Attestation API

This repository contains the App Attestation API, which is deployed as an AWS Lambda service.
It is designed to verify the integrity of mobile applications using Google's Play Integrity API, and will be deployed to higher environments (e.g., UAT, Production) on AWS.



### Setup Requirements
* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* Python - [Python 3.11 installed](https://www.python.org/downloads/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)


### Setup Local Environment
- Create Environment:
`python3.11 -m venv .app-attestation-venv`
- Activate Virtual Environment:
`source .app-attestation-venv/bin/activate`
- Update/Create environment variables:
  - Create or update `/app/.env` file for docker services. Refer to `/app/.env.example`
  - Update `template.yaml` environment variables for lambda.
- Install Packages
`pip install -r app/requirements.txt`
- If using VS Code, Update Python Interpreter:
  - Open Commands `cmd + shift + p`
  - Select `Python: Select Intepreter`
  - Select `Python 3.11 (.app-attestation-venv)`


### Build and Run Local Application

#### Using SAM CLI (Lambda)

- Build service to reflect new changes. Use debug mode to output more details while building:
```bash
sam build -t local.template.yaml --use-container
```
- Start API:
```bash
sam local start-api -t .aws-sam/build/template.yaml
```
- Access API:
`http://localhost:3000/<endpoint>`
- Health Check:
`http://localhost:3000/health_check`
- Curl:
`curl -i -H "x-api-key: dev-local-key-123" http://127.0.0.1:3000/health_check`
- Verify Android Integrity:
`curl -i -X POST -H "x-api-key: dev-local-key-123" -H "Content-Type: application/json" -d '{"integrity_token": "<token>"}' http://127.0.0.1:3000/android/verify-integrity`


### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health_check` | None | Service health check |
| POST | `/android/verify-integrity` | X-Api-Key | Verify Android Play Integrity token |

#### Android Verify Integrity Request Body
```json
{
  "integrity_token": "string (required)",
  "nonce": "string (optional)",
  "package_name": "string (optional)"
}
```


### Run Tests
```bash
pytest app/test/test_android_integrity.py
```


### Dependency References

This project relies on the following Python libraries:

- **requests**
  Used for making HTTP requests to external APIs.
  Documentation: [https://docs.python-requests.org/](https://docs.python-requests.org/)

- **boto3** (AWS SDK for Python)
  Used for interacting with AWS services such as Secrets Manager and SSM.
  Documentation: [https://boto3.amazonaws.com/](https://boto3.amazonaws.com/)

- **pydantic**
  Used for data validation and settings management with Python type hints.
  Documentation: [https://docs.pydantic.dev/](https://docs.pydantic.dev/)

- **google-auth**
  Used for authenticating with Google APIs via OAuth2 service accounts.
  Documentation: [https://google-auth.readthedocs.io/](https://google-auth.readthedocs.io/)

- **python-dotenv**
  Used for loading environment variables from `.env` files.
  Documentation: [https://saurabh-kumar.com/python-dotenv/](https://saurabh-kumar.com/python-dotenv/)

- **aws-secretsmanager-caching**
  Used for caching AWS Secrets Manager values in Lambda to reduce API calls.
  Documentation: [https://github.com/aws/aws-secretsmanager-caching-python](https://github.com/aws/aws-secretsmanager-caching-python)


### Code Structure
```bash
├── .gitignore
├── .gitlab-ci.yml
├── README.md
├── app
│   ├── .env.example
│   ├── __init__.py
│   ├── app_logger.py
│   ├── authorizer.py
│   ├── aws_library.py
│   ├── config_loader.py
│   ├── constants.py
│   ├── main.py
│   ├── requirements.txt
│   ├── settings.py
│   ├── handler
│   │   └── attestation
│   │       ├── __init__.py
│   │       └── android_integrity_handler.py
│   ├── integrations
│   │   ├── __init__.py
│   │   ├── aws_secret_manager_boto_client.py
│   │   ├── aws_secret_manager_client.py
│   │   └── google
│   │       ├── __init__.py
│   │       └── play_integrity_client.py
│   ├── schema
│   │   ├── __init__.py
│   │   └── android_integrity.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── android_integrity_service.py
│   │   └── health_check_service.py
│   ├── test
│   │   ├── __init__.py
│   │   └── test_android_integrity.py
│   └── utilities
│       ├── __init__.py
│       ├── json_request_util.py
│       ├── logger_util.py
│       ├── parse_lambda_event.py
│       └── request_util.py
├── deployment
│   ├── dev.template.yaml
│   └── prod.template.yaml
├── pytest.ini
├── local.template.yaml
├── template.yaml
```


### Development Standards
- In VS Code:
  - Set Python: Pylance in `Configure Language Specific Settings` > Text Editor > Editor: Default Formatter. This is good for deprecated function hints.
  - Add Black Formatter Extension. Set it as manual Code Formatter.
# app-attestation-api
