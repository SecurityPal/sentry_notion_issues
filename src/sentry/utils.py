import hashlib
import hmac
import logging
from typing import Optional

from fastapi import HTTPException, Request

from settings import settings

logger = logging.getLogger(__name__)


def is_correct_sentry_signature(
    body: bytes, key: str, expected: Optional[str] = None
) -> bool:
    # expected could be `None` if the header was missing,
    # in which case we return early as the request is invalid
    # without a signature
    if not expected:
        return False

    digest = hmac.new(
        key=key.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(digest, expected):
        return False

    logger.info("Authorized: Verified request came from Sentry")
    return True


async def verify_sentry_signature(request: Request):
    """
    Dependency function to authenticate that requests are coming from Sentry.
    Raises HTTPException if the signature is invalid.

    Args:
        request: The FastAPI Request object to verify
    """
    # We need to read the raw body
    body = await request.body()

    # Get client secret from settings
    client_secret = settings.sentry_notion_integration_client_secret or ""

    # The signature header may be one of these two values
    is_valid = is_correct_sentry_signature(
        body=body,
        key=client_secret,
        expected=request.headers.get("sentry-hook-signature"),
    ) or is_correct_sentry_signature(
        body=body,
        key=client_secret,
        expected=request.headers.get("sentry-app-signature"),
    )

    if not is_valid:
        logger.warning("Unauthorized: Invalid Sentry signature.")
        raise HTTPException(status_code=401, detail="Invalid Sentry Signature")

    # If valid, the dependency succeeds, and execution continues
    # No explicit return is needed
