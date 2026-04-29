import json
import logging
from typing import Tuple

from app_logger import get_logger
from constants import HttpStatus
from handler.attestation.android_integrity_handler import AndroidIntegrityHandler
from integrations.google.play_integrity_client import PlayIntegrityClient
from schema.android_integrity import (
    AndroidIntegrityResponse,
    IntegrityVerdict,
    TokenPayload,
)
from settings import google_settings
from utilities.parse_lambda_event import ParseLambdaEvent


# App recognition verdict constants
APP_VERDICT_PLAY_RECOGNIZED = "PLAY_RECOGNIZED"
APP_VERDICT_UNRECOGNIZED_VERSION = "UNRECOGNIZED_VERSION"
APP_VERDICT_UNATTEMPTED = "UNATTEMPTED"

# Device integrity verdict constants
DEVICE_VERDICT_MEETS_STRONG_INTEGRITY = "MEETS_STRONG_INTEGRITY"
DEVICE_VERDICT_MEETS_DEVICE_INTEGRITY = "MEETS_DEVICE_INTEGRITY"
DEVICE_VERDICT_MEETS_BASIC_INTEGRITY = "MEETS_BASIC_INTEGRITY"
DEVICE_VERDICT_MEETS_VIRTUAL_INTEGRITY = "MEETS_VIRTUAL_INTEGRITY"

# Account licensing verdict constants
LICENSE_VERDICT_LICENSED = "LICENSED"
LICENSE_VERDICT_UNLICENSED = "UNLICENSED"
LICENSE_VERDICT_UNATTEMPTED = "UNATTEMPTED"

# Minimum acceptable device verdicts (ordered from strongest to weakest)
ACCEPTABLE_DEVICE_VERDICTS = {
    DEVICE_VERDICT_MEETS_STRONG_INTEGRITY,
    DEVICE_VERDICT_MEETS_DEVICE_INTEGRITY,
    DEVICE_VERDICT_MEETS_BASIC_INTEGRITY,
}


class AndroidIntegrityService:
    """Service layer for Android Play Integrity API verification.

    Orchestrates the full verification flow:
    1. Validate the incoming request via the handler.
    2. Resolve the package name and Google credentials.
    3. Call the Play Integrity client to decode the token.
    4. Evaluate the returned verdicts.
    5. Return a structured HTTP response.
    """

    def __init__(self, logger: logging.Logger = None):
        self._logger = logger or get_logger()

    def _get_service_account_info(self) -> dict:
        """Parses the service account JSON from settings.

        Returns:
            Parsed service account dict, or empty dict on failure.
        """
        raw_json = google_settings.GOOGLE_SERVICE_ACCOUNT_JSON
        print("raw_json: ", raw_json)
        if not raw_json:
            self._logger.error("[AndroidIntegrityService] GOOGLE_SERVICE_ACCOUNT_JSON is not configured.")
            return {}
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as e:
            self._logger.error(f"[AndroidIntegrityService] Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
            return {}

    def _is_verdict_passing(self, payload: TokenPayload) -> bool:
        """Evaluates whether the token payload meets integrity requirements.

        Rules:
        - appRecognitionVerdict must be PLAY_RECOGNIZED.
        - deviceRecognitionVerdict must contain at least one acceptable verdict.

        Args:
            payload: Decoded token payload.

        Returns:
            True if all required verdicts pass.
        """
        app_verdict = payload.appIntegrity.appRecognitionVerdict if payload.appIntegrity else None

        device_verdicts = []
        if payload.deviceIntegrity and payload.deviceIntegrity.deviceRecognitionVerdict:
            device_verdicts = payload.deviceIntegrity.deviceRecognitionVerdict

        app_ok = app_verdict == APP_VERDICT_PLAY_RECOGNIZED
        device_ok = bool(set(device_verdicts) & ACCEPTABLE_DEVICE_VERDICTS)

        self._logger.info(
            f"[AndroidIntegrityService] Verdict check — "
            f"app_verdict={app_verdict} app_ok={app_ok} | "
            f"device_verdicts={device_verdicts} device_ok={device_ok}"
        )

        return app_ok and device_ok

    def verify(self, event: dict) -> Tuple[int, dict]:
        """Entry point called by main.py for POST /android/verify-integrity.

        Args:
            event: Raw Lambda event dict.

        Returns:
            Tuple of (HTTP status code, response body dict).
        """
        request_id = ParseLambdaEvent.get_request_id(event)

        # 1. Parse and validate request
        handler = AndroidIntegrityHandler(request_id=request_id, event=event)
        if not handler.validate():
            return handler.get_error_response()

        request = handler.get_request()

        # 2. Resolve package name (request body overrides settings)
        package_name = request.package_name or google_settings.ANDROID_PACKAGE_NAME
        print("package_name: ", package_name)
        if not package_name:
            return HttpStatus.HTTP_500, {"message": "ANDROID_PACKAGE_NAME is not configured."}

        # 3. Load Google service account credentials
        service_account_info = self._get_service_account_info()
        if not service_account_info:
            return HttpStatus.HTTP_500, {"message": "Google service account credentials are not configured."}

        # 4. Call Play Integrity API
        client = PlayIntegrityClient(
            service_account_info=service_account_info,
            package_name=package_name,
            logger=self._logger,
        )
        result = client.decode_integrity_token(integrity_token=request.integrity_token)

        if not result["is_success"]:
            self._logger.error(
                f"[AndroidIntegrityService] Play Integrity API call failed: {result.get('error')}"
            )
            return HttpStatus.HTTP_500, {
                "message": "Failed to verify integrity token.",
                "error": result.get("error"),
            }

        # 5. Parse token payload
        raw_payload = result["data"]
        try:
            payload = TokenPayload(**raw_payload)
        except Exception as e:
            self._logger.error(f"[AndroidIntegrityService] Failed to parse token payload: {e}")
            return HttpStatus.HTTP_500, {"message": "Failed to parse integrity token payload."}

        # 6. Optional nonce validation
        if request.nonce:
            returned_nonce = payload.requestDetails.nonce if payload.requestDetails else None
            if returned_nonce != request.nonce:
                self._logger.warning(
                    f"[AndroidIntegrityService] Nonce mismatch. "
                    f"Expected={request.nonce} Got={returned_nonce}"
                )
                return HttpStatus.HTTP_400, {"message": "Nonce mismatch. Token may have been replayed."}

        # 7. Evaluate verdicts
        is_verified = self._is_verdict_passing(payload)

        verdict = IntegrityVerdict(
            app_recognition=payload.appIntegrity.appRecognitionVerdict if payload.appIntegrity else None,
            device_recognition=payload.deviceIntegrity.deviceRecognitionVerdict if payload.deviceIntegrity else None,
            app_licensing=payload.accountDetails.appLicensingVerdict if payload.accountDetails else None,
        )

        details = {
            "package_name": payload.appIntegrity.packageName if payload.appIntegrity else None,
            "version_code": payload.appIntegrity.versionCode if payload.appIntegrity else None,
            "timestamp_millis": payload.requestDetails.timestampMillis if payload.requestDetails else None,
            "nonce": payload.requestDetails.nonce if payload.requestDetails else None,
        }

        response = AndroidIntegrityResponse(
            is_verified=is_verified,
            verdict=verdict,
            details=details,
            message="Integrity verified successfully." if is_verified else "Integrity check failed.",
        )

        status_code = HttpStatus.HTTP_200 if is_verified else HttpStatus.HTTP_403
        return status_code, response.model_dump()


# Module-level singleton
_android_integrity_service = AndroidIntegrityService()


def get_android_integrity_service() -> AndroidIntegrityService:
    return _android_integrity_service
