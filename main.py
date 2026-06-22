import time
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, status, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

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
\nSince this API is currently only meant to be accessed by the LangOps Website frontend, and is not meant for public consumption, there is no public-facing URL at this time. 
Any apps which need access to the API are assumed to be operating on the LangOps Server Cluster, within the same virtual network, and should communicate with the API that way.

## How Authentication Works  

1. **Token:** Every request sent to protected endpoints must include the **`CF_Authorization`** HTTP header containing a valid JSON Web Token (JWT) issued by Cloudflare Access.
2. **Cryptographic Verification:** The API extracts this token and dynamically fetches Cloudflare's public keys via the JSON Web Key Set (JWKS) endpoint (`/cdn-cgi/access/certs`). The signature is cryptographically validated using the **RS256** asymmetric algorithm.
3. **Issuer & Lifecycle Enforcement:** The API strict-matches the token issuer (`iss`) against the PCG LangOps Cloudflare Team Domain URL and ensures the token's execution timestamp (`exp`) has not expired.
4. **Audience Constraints:** To prevent token-spoofing across applications, the API validates the token's Audience Tag (`aud`). The token must match one of our whitelisted environment targets:
   - **Frontend Web Application Audience** (`LANGOPS_WEBSITE_AUD_TAG`)
   - **Standalone API Gateway Audience** (`API_AUD_TAG`)

\nMore audiences may be provisioned upon request. **Any request from an app not in the list of trusted audience tags will result in an error (401 Unauthorized).** 
If you require access, please contact the maintainers.

# 🛠️ Operations Currently Supported
1. **Status**: Here you can check the current database version and connection health
2. **Products**: This is the main function of the API. It can return all LangOps products matching any supported criteria, including:
    - Target language
    - Date published (from and to)  
    - Product code
    - Media Groups
    - Published only, unpublished only, or deleted only
    **Note that this endpoint is paginated and has a limit of 500.**

3. **IDML File Operations**: This allows management of the translation lifecycle of Adobe inDesign files. 
They can be parsed into XLIFF files for Crowdin upload. Once translated, the XLIFF files can be re-imported into the .idml file.
---
"""

app = FastAPI(title="PCG LangOps API", description=auth_docs_blurb, version="0.5.0")
logger = logging.getLogger("uvicorn.error")

# -------------------
# API ROUTES
# -------------------
GENERAL_PREFIX = "/api/v1"

app.include_router(apistatus.router, prefix=f"{GENERAL_PREFIX}/status", tags=["API Status"], dependencies=[Depends(verify_jwt)])
app.include_router(products.router, prefix=f"{GENERAL_PREFIX}/products", tags=["Products"], dependencies=[Depends(verify_jwt)])
app.include_router(idml.router, prefix=f"{GENERAL_PREFIX}/idml", tags=["IDML Operations"],dependencies=[Depends(verify_jwt)])



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
        f"API_REQUEST | User: {user} | Method: {request.method} | Path: {request.url.path} "
        f"| Status: {response.status_code} | Duration: {process_time:.2f}ms"
    )
    
    return response



# -------------------
# EXCEPTION HANDLERS
# -------------------


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exception: StarletteHTTPException):
    # Map specific status codes to your matching schema shapes
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
                "error_code": "HTTP_ERROR",
                "message": str(exception.detail),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    return JSONResponse(
        status_code=exception.status_code,
        content=payload.model_dump(mode="json")
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
        content=payload.model_dump(mode="json")
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
        content=payload.model_dump(mode="json")
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
        content=payload.model_dump(mode="json")
    )