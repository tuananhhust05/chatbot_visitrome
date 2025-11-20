from functools import wraps
# from flask import current_app, jsonify, request
from fastapi import Request, Depends, HTTPException
from app.config import get_settings
import logging
import hashlib
import hmac


def validate_signature(payload, signature, settings):
    """
    Validate the incoming payload's signature against our expected signature
    """
    # Use the App Secret to hash the payload
    expected_signature = hmac.new(
        bytes(settings.APP_SECRET, "latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Check if the signature matches
    return hmac.compare_digest(expected_signature, signature)


def signature_required(f):
    """
    Decorator to ensure that the incoming requests to our webhook are valid and signed with the correct signature.
    """
    @wraps(f)
    async def decorated_function(request: Request, settings = Depends(get_settings), *args, **kwargs):
        signature = request.headers.get("X-Hub-Signature-256", "")[7:]  # Removing 'sha256='
        body = await request.body()
        if not validate_signature(body.decode("utf-8"), signature, settings):
            logging.info("Signature verification failed!")
            return HTTPException(
                detail="Invalid signature",
                status_code=403,
            )
        return await f(request=request, settings=settings, *args, **kwargs)

    return decorated_function
