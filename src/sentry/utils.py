import hashlib
import hmac
import logging
import functools
from typing import Optional, Callable

from fastapi import Request, HTTPException

from settings import settings

logger = logging.getLogger(__name__)


def is_correct_sentry_signature(body: bytes, key: str, expected: Optional[str]) -> bool:
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


async def verify_sentry_signature(request: Request) -> bool:
    """
    This function will authenticate that the requests are coming from Sentry.
    It allows us to be confident that requests are using verified data sent directly from Sentry.

    Args:
        request: The FastAPI Request object to verify

    Returns:
        bool: True if the request has a valid Sentry signature, False otherwise
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
        logger.info("Unauthorized: Could not verify request came from Sentry")

    return is_valid


def require_sentry_signature(func: Callable) -> Callable:
    """
    Decorator to require a valid Sentry signature for a FastAPI endpoint.
    
    Args:
        func: The FastAPI endpoint function to decorate
        
    Returns:
        The decorated function that will check for a valid Sentry signature
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import asyncio
        
        # Get the request object from FastAPI's dependency injection
        # In FastAPI, the request is automatically passed to the endpoint
        request = kwargs.get('request')
        
        # If it's not in kwargs, check if it's in args
        if request is None:
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
        
        # If we still can't find the request, raise an error
        if request is None:
            raise HTTPException(status_code=500, detail="Request object not found")
        
        # Handle the async verification in a sync context
        loop = asyncio.get_event_loop()
        is_valid = loop.run_until_complete(verify_sentry_signature(request))
        
        if not is_valid:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Call the original function
        return func(*args, **kwargs)
    
    return wrapper
