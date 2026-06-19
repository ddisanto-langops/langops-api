import logging
from datetime import datetime, timezone
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError, ResponseValidationError

from schemas.error_schemas import (
    ErrorDetail, 
    ClientValidationError, 
    ServerContractViolation,
    BadRequestError,
    NotFoundError
)
from routers import products, idml, apistatus


app = FastAPI(title="PCG LangOps API")


# -------------------
# API ROUTES
# -------------------
GENERAL_PREFIX = "/api/v1"

app.include_router(apistatus.router, prefix=f"{GENERAL_PREFIX}/status", tags=["API Status"])
app.include_router(products.router, prefix=f"{GENERAL_PREFIX}/products", tags=["Products"])
app.include_router(idml.router, prefix=f"{GENERAL_PREFIX}/idml", tags=["IDML Operations"])


# -------------------
# EXCEPTION HANDLERS
# -------------------

logger = logging.getLogger("uvicorn.error")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exception: HTTPException):
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
        content=payload.model_dump()
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
        content=payload.model_dump()
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
        timestamp= datetime.now(timezone.utc).isoformat()
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=payload.model_dump()
    )


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request: Request, exception: ResponseValidationError):
    payload = ServerContractViolation(
        error_code="SERVER_CONTRACT_VIOLATION",
        message="Internal server data configuration error.",
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload.model_dump()
    )