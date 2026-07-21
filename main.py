import time
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, status, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas.base import CamelJSONResponse
from schemas.error_schemas import (
    ErrorDetail, 
    ClientValidationError, 
    ServerContractViolation,
    BadRequestError,
    NotFoundError
)
from routers import products, idml, apistatus
from auth import verify_jwt

auth_docs_blurb = """
# 🔐 Authentication & Zero Trust Architecture

This API is protected behind a **Cloudflare Zero Trust** perimeter layer and enforces strict identity verification using asymmetric cryptography. It cannot be accessed anonymously.

## General Authentication  
**To access the API, the caller must meet 3 conditions:**
1. Valid Cloudflare service auth
```html
"CF-Access-Client-Id: <id>"
"CF-Access-Client-Secret: <token>"
```
2. The `iss` (issuer) claim of the JWT must match the expected Cloudflare team URL
3. The request must originate from an approved audience  
Cloudflare's JWTs have an `aud` claim, which must match at least one entry in the pre-configured list.
\nAudiences currently supported:
- LangOps API over HTTPS
- LangOps website
- LangOps Gateway
\n Any other apps must be provisioned via request. **Any request from an app not in the list of trusted audience tags will result in an error (401 Unauthorized).**

# 🛠️ Operations Currently Supported
1. **Status**: Here you can check the current database version and connection health
2. **Products**: This is the main function of the API. It can return all LangOps products matching any supported criteria, including:
    - Target language
    - Date published (from and to)  
    - Product code
    - Media Groups
    - Published only, unpublished only, or deleted only  
    **Note 1: this endpoint is paginated and has a limit of 500.**  
    **Note 2: To avoid duplicates and unpredictable logic, end-users are not allowed to directly add products. They should do so via the source of truth in a dedicated frontend with proper validation logic.**

3. **IDML Operations**: This allows labeling of Adobe inDesign strings by story provenance to avoid context-loss.
---
"""

app = FastAPI(title="PCG LangOps API", description=auth_docs_blurb, version="1.0.5", default_response_class=CamelJSONResponse)
logger = logging.getLogger("uvicorn.error")

# -------------------
# API ROUTES
# -------------------
GENERAL_PREFIX = "/api/v1"

app.include_router(apistatus.router, prefix=f"{GENERAL_PREFIX}/status", tags=["API Status"], dependencies=[Depends(verify_jwt)])
app.include_router(products.router, prefix=f"{GENERAL_PREFIX}/products", tags=["Products"], dependencies=[Depends(verify_jwt)])
app.include_router(idml.router, prefix=f"{GENERAL_PREFIX}/idml", tags=["IDML Operations"], dependencies=[Depends(verify_jwt)])



# -------------------
# MIDDLEWARE
# -------------------

@app.middleware("http")
async def log(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000

    user = getattr(request.state, "user_email", "Unknown")

    logger.info(
        f"{datetime.now(timezone.utc)} | User: {user} | Method: {request.method} | Path: {request.url.path} "
        f"| Status: {response.status_code} | Duration: {process_time:.2f}ms"
    )
    
    return response



# -------------------
# EXCEPTION HANDLERS
# -------------------


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exception: StarletteHTTPException):
    logger.error(f"HTTP EXCEPTION TRIGGERED: Status {exception.status_code} | Detail: {exception.detail}")
    if exception.status_code == status.HTTP_404_NOT_FOUND:
        payload = NotFoundError(
            error_code="NOT_FOUND",
            message=str(exception.detail),
            timestamp=datetime.now(timezone.utc)
        )
    elif exception.status_code == status.HTTP_400_BAD_REQUEST:
        payload = BadRequestError(
            error_code="BAD_REQUEST",
            message=str(exception.detail),
            timestamp=datetime.now(timezone.utc)
        )
    else:
        # Fallback handle for other explicitly raised HTTP exceptions (e.g., 401, 403)
        return JSONResponse(
            status_code=exception.status_code,
            content={
                "error_code": f"HTTP_{exception.status_code}",
                "message": str(exception.detail),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    return JSONResponse(
        status_code=exception.status_code,
        content=payload.model_dump(mode="json", by_alias=True)
    )



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    details = [
        ErrorDetail(
            loc=error["loc"],
            msg=error["msg"],
            type=error["type"]
        )
        for error in exception.errors()
    ]

    payload = ClientValidationError(
        error_code = "INVALID_INPUT_PAYLOAD",
        message = "Internal server data configuration error",
        details = details,
        timestamp= datetime.now(timezone.utc)
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=payload.model_dump(mode="json", by_alias=True)
    )


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request: Request, exception: ResponseValidationError):
    payload = ServerContractViolation(
        error_code="SERVER_CONTRACT_VIOLATION",
        message="Internal server data configuration error.",
        timestamp=datetime.now(timezone.utc)
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload.model_dump(mode="json", by_alias=True)
    )



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exception: Exception):
    logger.error(f"Unhandled system error: {exception}", exc_info=True)

    payload = ServerContractViolation(
        error_code="SERVER_CONTRACT_VIOLATION",
        message="An unexpected system error occurred on our end.",
        timestamp=datetime.now(timezone.utc)
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload.model_dump(mode="json", by_alias=True)
    )