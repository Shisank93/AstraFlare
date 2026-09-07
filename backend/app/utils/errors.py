"""
Custom HTTP Exceptions and Error Handlers for AstraFlare API.
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("astraflare.backend.errors")

class HotspotNotFoundException(HTTPException):
    def __init__(self, hotspot_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotspot with ID '{hotspot_id}' was not found in database."
        )

class IndustrialSiteNotFoundException(HTTPException):
    def __init__(self, site_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Industrial site with ID '{site_id}' was not found."
        )

class InvalidCoordinateException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message
        )

class ServiceUnavailableException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact system administrator."}
    )
