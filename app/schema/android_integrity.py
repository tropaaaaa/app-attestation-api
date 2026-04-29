from typing import List, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Request
# ──────────────────────────────────────────────

class AndroidIntegrityRequest(BaseModel):
    """Payload sent by the Android client to our verify endpoint."""

    integrity_token: str = Field(..., description="Integrity token returned by the Android Play Integrity API.")
    nonce: Optional[str] = Field(None, description="Nonce used when requesting the token. Used for validation.")
    package_name: Optional[str] = Field(None, description="Override the package name from settings (optional).")

    class Config:
        extra = "ignore"


# ──────────────────────────────────────────────
# Google Play Integrity verdict sub-models
# ──────────────────────────────────────────────

class RequestDetails(BaseModel):
    """Details about the original integrity request."""

    requestPackageName: Optional[str] = None
    nonce: Optional[str] = None
    timestampMillis: Optional[str] = None
    requestHash: Optional[str] = None


class AppIntegrity(BaseModel):
    """App-level integrity verdict."""

    appRecognitionVerdict: Optional[str] = None
    packageName: Optional[str] = None
    certificateSha256Digest: Optional[List[str]] = None
    versionCode: Optional[str] = None


class DeviceIntegrity(BaseModel):
    """Device-level integrity verdict."""

    deviceRecognitionVerdict: Optional[List[str]] = None


class AccountDetails(BaseModel):
    """Account-level integrity verdict."""

    appLicensingVerdict: Optional[str] = None


class TokenPayload(BaseModel):
    """Full decoded token payload from Google Play Integrity API."""

    requestDetails: Optional[RequestDetails] = None
    appIntegrity: Optional[AppIntegrity] = None
    deviceIntegrity: Optional[DeviceIntegrity] = None
    accountDetails: Optional[AccountDetails] = None


# ──────────────────────────────────────────────
# Response
# ──────────────────────────────────────────────

class IntegrityVerdict(BaseModel):
    """Simplified verdict summary returned to the client."""

    app_recognition: Optional[str] = None
    device_recognition: Optional[List[str]] = None
    app_licensing: Optional[str] = None


class AndroidIntegrityResponse(BaseModel):
    """Response returned by the verify-integrity endpoint."""

    is_verified: bool
    verdict: Optional[IntegrityVerdict] = None
    details: Optional[dict] = None
    message: Optional[str] = None
