"""Unit tests for Android Play Integrity API verification flow."""
import json
import pytest
from unittest.mock import MagicMock, patch

from constants import HttpStatus
from handler.attestation.android_integrity_handler import AndroidIntegrityHandler
from services.android_integrity_service import AndroidIntegrityService
from schema.android_integrity import (
    AndroidIntegrityRequest,
    TokenPayload,
    AppIntegrity,
    DeviceIntegrity,
    AccountDetails,
    RequestDetails,
)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _make_event(body: dict, headers: dict = None) -> dict:
    return {
        "httpMethod": "POST",
        "path": "/android/verify-integrity",
        "headers": {**(headers or {}), "content-type": "application/json"},
        "body": json.dumps(body),
        "isBase64Encoded": False,
        "requestContext": {"requestId": "test-request-id-123"},
    }


def _make_valid_payload() -> dict:
    return {
        "requestDetails": {
            "requestPackageName": "com.example.myapp",
            "nonce": "abc123",
            "timestampMillis": "1700000000000",
        },
        "appIntegrity": {
            "appRecognitionVerdict": "PLAY_RECOGNIZED",
            "packageName": "com.example.myapp",
            "certificateSha256Digest": ["abc123"],
            "versionCode": "1",
        },
        "deviceIntegrity": {
            "deviceRecognitionVerdict": ["MEETS_DEVICE_INTEGRITY"],
        },
        "accountDetails": {
            "appLicensingVerdict": "LICENSED",
        },
    }


# ──────────────────────────────────────────────
# Handler tests
# ──────────────────────────────────────────────

class TestAndroidIntegrityHandler:

    def test_valid_request_passes_validation(self):
        event = _make_event({"integrity_token": "valid-token-abc"})
        h = AndroidIntegrityHandler(request_id="req-1", event=event)
        assert h.validate() is True
        assert h.get_request().integrity_token == "valid-token-abc"

    def test_missing_integrity_token_fails_validation(self):
        event = _make_event({})
        h = AndroidIntegrityHandler(request_id="req-2", event=event)
        assert h.validate() is False
        assert h.get_error() is not None

    def test_empty_body_fails_validation(self):
        event = {
            "httpMethod": "POST",
            "path": "/android/verify-integrity",
            "headers": {"content-type": "application/json"},
            "body": "",
            "isBase64Encoded": False,
            "requestContext": {"requestId": "req-3"},
        }
        h = AndroidIntegrityHandler(request_id="req-3", event=event)
        assert h.validate() is False

    def test_optional_nonce_and_package_name_are_accepted(self):
        event = _make_event({
            "integrity_token": "token-xyz",
            "nonce": "my-nonce",
            "package_name": "com.custom.app",
        })
        h = AndroidIntegrityHandler(request_id="req-4", event=event)
        assert h.validate() is True
        req = h.get_request()
        assert req.nonce == "my-nonce"
        assert req.package_name == "com.custom.app"

    def test_error_response_returns_400(self):
        event = _make_event({})
        h = AndroidIntegrityHandler(request_id="req-5", event=event)
        h.validate()
        status, body = h.get_error_response()
        assert status == HttpStatus.HTTP_400
        assert "message" in body


# ──────────────────────────────────────────────
# Schema tests
# ──────────────────────────────────────────────

class TestAndroidIntegritySchema:

    def test_token_payload_parses_correctly(self):
        payload = TokenPayload(**_make_valid_payload())
        assert payload.appIntegrity.appRecognitionVerdict == "PLAY_RECOGNIZED"
        assert "MEETS_DEVICE_INTEGRITY" in payload.deviceIntegrity.deviceRecognitionVerdict
        assert payload.accountDetails.appLicensingVerdict == "LICENSED"
        assert payload.requestDetails.nonce == "abc123"

    def test_token_payload_handles_missing_optional_fields(self):
        payload = TokenPayload()
        assert payload.appIntegrity is None
        assert payload.deviceIntegrity is None


# ──────────────────────────────────────────────
# Service tests
# ──────────────────────────────────────────────

class TestAndroidIntegrityService:

    def _make_service(self):
        logger = MagicMock()
        return AndroidIntegrityService(logger=logger)

    def test_is_verdict_passing_with_valid_payload(self):
        service = self._make_service()
        payload = TokenPayload(**_make_valid_payload())
        assert service._is_verdict_passing(payload) is True

    def test_is_verdict_passing_fails_for_unrecognized_app(self):
        service = self._make_service()
        data = _make_valid_payload()
        data["appIntegrity"]["appRecognitionVerdict"] = "UNRECOGNIZED_VERSION"
        payload = TokenPayload(**data)
        assert service._is_verdict_passing(payload) is False

    def test_is_verdict_passing_fails_for_no_device_integrity(self):
        service = self._make_service()
        data = _make_valid_payload()
        data["deviceIntegrity"]["deviceRecognitionVerdict"] = []
        payload = TokenPayload(**data)
        assert service._is_verdict_passing(payload) is False

    @patch("services.android_integrity_service.google_settings")
    @patch("services.android_integrity_service.PlayIntegrityClient")
    def test_verify_returns_200_on_valid_token(self, MockClient, mock_settings):
        mock_settings.ANDROID_PACKAGE_NAME = "com.example.myapp"
        mock_settings.GOOGLE_SERVICE_ACCOUNT_JSON = json.dumps({"type": "service_account"})

        mock_instance = MagicMock()
        mock_instance.decode_integrity_token.return_value = {
            "is_success": True,
            "data": _make_valid_payload(),
            "error": None,
        }
        MockClient.return_value = mock_instance

        service = self._make_service()
        event = _make_event({"integrity_token": "valid-token"})
        status_code, body = service.verify(event)

        assert status_code == HttpStatus.HTTP_200
        assert body["is_verified"] is True

    @patch("services.android_integrity_service.google_settings")
    @patch("services.android_integrity_service.PlayIntegrityClient")
    def test_verify_returns_403_when_verdict_fails(self, MockClient, mock_settings):
        mock_settings.ANDROID_PACKAGE_NAME = "com.example.myapp"
        mock_settings.GOOGLE_SERVICE_ACCOUNT_JSON = json.dumps({"type": "service_account"})

        failing_payload = _make_valid_payload()
        failing_payload["appIntegrity"]["appRecognitionVerdict"] = "UNATTEMPTED"

        mock_instance = MagicMock()
        mock_instance.decode_integrity_token.return_value = {
            "is_success": True,
            "data": failing_payload,
            "error": None,
        }
        MockClient.return_value = mock_instance

        service = self._make_service()
        event = _make_event({"integrity_token": "bad-token"})
        status_code, body = service.verify(event)

        assert status_code == HttpStatus.HTTP_403
        assert body["is_verified"] is False

    @patch("services.android_integrity_service.google_settings")
    def test_verify_returns_400_on_missing_token(self, mock_settings):
        mock_settings.ANDROID_PACKAGE_NAME = "com.example.myapp"
        mock_settings.GOOGLE_SERVICE_ACCOUNT_JSON = json.dumps({"type": "service_account"})

        service = self._make_service()
        event = _make_event({})
        status_code, body = service.verify(event)

        assert status_code == HttpStatus.HTTP_400

    @patch("services.android_integrity_service.google_settings")
    @patch("services.android_integrity_service.PlayIntegrityClient")
    def test_verify_returns_400_on_nonce_mismatch(self, MockClient, mock_settings):
        mock_settings.ANDROID_PACKAGE_NAME = "com.example.myapp"
        mock_settings.GOOGLE_SERVICE_ACCOUNT_JSON = json.dumps({"type": "service_account"})

        mock_instance = MagicMock()
        mock_instance.decode_integrity_token.return_value = {
            "is_success": True,
            "data": _make_valid_payload(),  # payload nonce = "abc123"
            "error": None,
        }
        MockClient.return_value = mock_instance

        service = self._make_service()
        event = _make_event({"integrity_token": "token", "nonce": "wrong-nonce"})
        status_code, body = service.verify(event)

        assert status_code == HttpStatus.HTTP_400
        assert "Nonce mismatch" in body["message"]
