# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Build and run locally (requires Docker):**
```bash
sam build -t local.template.yaml --use-container
sam local start-api -t .aws-sam/build/template.yaml
```

**Run tests:**
```bash
pytest app/test/test_android_integrity.py
```

**Test API locally:**
```bash
curl -i -H "x-api-key: dev-local-key-123" http://127.0.0.1:3000/health_check

curl -i -X POST \
  -H "x-api-key: dev-local-key-123" \
  -H "Content-Type: application/json" \
  -d '{"integrity_token": "<token>"}' \
  http://127.0.0.1:3000/android/verify-integrity
```

## Architecture

AWS Lambda microservice that verifies Android app integrity via Google's Play Integrity API. Requests flow through a layered pattern:

```
API Gateway → main.handler()
  → ParseLambdaEvent (extracts method/path/headers/body from Lambda event)
  → validate_api_key() (X-Api-Key header check)
  → Handler (Pydantic schema validation)
  → Service (business logic)
  → Integration (Google Play Integrity API call)
  → Response
```

**Layer responsibilities:**
- `app/main.py` — Lambda entry point; routes by method + path
- `app/handler/` — Request body validation using Pydantic schemas
- `app/services/` — Orchestration; loads credentials, calls integrations, evaluates verdicts
- `app/integrations/` — External API clients (Google Play Integrity, AWS Secrets Manager)
- `app/schema/` — Pydantic models for requests, responses, and decoded token payloads
- `app/utilities/` — Lambda event parsing, HTTP client wrapper, logging, config loading

**Configuration loading** (`config_loader.py`): locally reads from `.env`; in deployed environments fetches from AWS Secrets Manager. Copy `.env.example` → `.env` for local dev.

**Verdict logic** (`android_integrity_service.py`): returns 200 if `appRecognitionVerdict == "PLAY_RECOGNIZED"` AND device has at least one of `MEETS_STRONG_INTEGRITY`, `MEETS_DEVICE_INTEGRITY`, or `MEETS_BASIC_INTEGRITY`; otherwise returns 403.

**Secrets Manager**: two clients exist — `AwsSecretManagerViaLambdaExtensionApi` (primary, via Lambda Layer) and `AwsSecretManagerViaBotoApi` (boto3 fallback).

**Deployment templates**: `template.yaml` (production), `local.template.yaml` (local dev with `dev-local-key-123` API key), `deployment/dev.template.yaml` and `deployment/prod.template.yaml`.

## API Endpoints

| Method | Path | Auth |
|--------|------|------|
| GET | `/health_check` | X-Api-Key header |
| POST | `/android/verify-integrity` | X-Api-Key header |
