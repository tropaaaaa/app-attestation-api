import json
import config_loader

from constants import HttpStatus
from services.health_check_service import HealthCheckService
from services.android_integrity_service import get_android_integrity_service
from utilities.parse_lambda_event import ParseLambdaEvent
from settings import system_settings


class UnauthorizedException(Exception):
    pass


POST = "POST"
GET = "GET"
DELETE = "DELETE"


def validate_api_key(event):
    headers = ParseLambdaEvent.get_request_header_dict(event)
    api_key = headers.get("X-Api-Key") or headers.get("x-api-key")
    expected_api_key = system_settings.X_API_KEY
    if not api_key or api_key != expected_api_key:
        raise UnauthorizedException("Invalid API key")


def safe_serialize(obj):
    """Convert objects like datetime to string for JSON serialization."""
    try:
        return json.dumps(obj, default=str)
    except Exception:
        return json.dumps({"error": "Unserializable response"})


def handler(event, context):
    http_method = ParseLambdaEvent.get_http_method_str(event)
    path = ParseLambdaEvent.get_path_str(event)
    request_id = ParseLambdaEvent.get_request_id(event=event)

    process_log = f"Request: {http_method} {path} | request_id={request_id}"
    print(f"{process_log} --Start")

    # Default response
    status_code = HttpStatus.HTTP_404
    response_body = {"message": "Not found"}

    # ── Health check (no auth required) ─────────────────────────────────────
    if path == "/health_check" and http_method == GET:
        status_code, response_body = HealthCheckService.get_details(event, context)
        return {
            "statusCode": status_code,
            "body": safe_serialize(response_body),
            "headers": {"Content-Type": "application/json"},
        }

    # ── Android - Play Integrity API ─────────────────────────────────────────
    if path == "/android/verify-integrity" and http_method == POST:
        android_integrity_service = get_android_integrity_service()
        status_code, response_body = android_integrity_service.verify(event)

    print(f"{response_body} --End")
    return {
        "statusCode": status_code,
        "body": safe_serialize(response_body),
        "headers": {"Content-Type": "application/json"},
    }
