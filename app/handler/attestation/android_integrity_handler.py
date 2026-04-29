from typing import Optional

from pydantic import ValidationError

from constants import HttpStatus
from schema.android_integrity import AndroidIntegrityRequest
from utilities.parse_lambda_event import ParseLambdaEvent


class AndroidIntegrityHandler:
    """Parses and validates the Lambda event for the Android integrity verify endpoint.

    Follows the Handler pattern from the project architecture:
    the handler is responsible for request extraction and validation before
    the service layer processes the business logic.
    """

    def __init__(self, request_id: str, event: dict):
        self._request_id = request_id
        self._event = event
        self._request: Optional[AndroidIntegrityRequest] = None
        self._error: Optional[str] = None

    def validate(self) -> bool:
        """Parses the request body and validates it against AndroidIntegrityRequest schema.

        Returns:
            True if valid, False otherwise. Access errors via get_error().
        """
        body = ParseLambdaEvent.get_request_body_dict(self._event)

        if not body or not isinstance(body, dict):
            self._error = "Request body is missing or not valid JSON."
            return False

        try:
            self._request = AndroidIntegrityRequest(**body)
        except ValidationError as e:
            errors = e.errors()
            first_error = errors[0] if errors else {}
            field = ".".join(str(loc) for loc in first_error.get("loc", []))
            msg = first_error.get("msg", "Validation error.")
            self._error = f"{field}: {msg}" if field else msg
            return False

        return True

    def get_request(self) -> Optional[AndroidIntegrityRequest]:
        return self._request

    def get_error(self) -> Optional[str]:
        return self._error

    def get_error_response(self):
        return HttpStatus.HTTP_400, {"message": self._error or "Bad request."}
