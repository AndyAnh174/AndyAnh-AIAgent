from fastapi import Depends, HTTPException, Request, status

from app.core.config import get_settings


async def validate_api_key(request: Request, settings=Depends(get_settings)) -> None:
    import logging
    logger = logging.getLogger(__name__)
    
    api_key = request.headers.get("x-api-key")
    valid_keys = settings.normalized_api_keys
    logger.debug("Received API key: %s, Valid keys: %s", api_key, valid_keys)
    
    if not api_key or api_key not in valid_keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

