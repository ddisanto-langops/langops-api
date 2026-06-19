from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import  text
from sqlalchemy.ext.asyncio import AsyncSession



from routers import products, idml

from schemas import (
    CheckHealthResponse, 
    ProductError
) 
from db import get_db

app = FastAPI(title="PCG LangOps API")

GENERAL_PREFIX = "/api"

app.include_router(products.router, prefix=f"{GENERAL_PREFIX}/products", tags=["Products"])
app.include_router(idml.router, prefix=f"{GENERAL_PREFIX}/idml", tags=["IDML Operations"])


@app.get(
    "/api/health",
    response_model=CheckHealthResponse,
    responses={
        500: { "model": ProductError, "response_description": "Internal server error" }
    }
)
async def check_health(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT version();"))
        db_version = result.scalar()
        return {
            "status": "OK",
            "database_version": db_version
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to get Postgres version: check that database is online. Message: {e}")
    












# -------------------
# EXCEPTION HANDLERS
# -------------------


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status_code": 422, "detail": exception.errors()[0]["msg"]}
    )

@app.exception_handler(StarletteHTTPException)
def general_exception_handler(request: Request, exception: StarletteHTTPException):
    return JSONResponse(
        status_code= exception.status_code,
        content = {
            "status_code": exception.status_code,
            "detail": exception.detail or "An unknown error has occurred",
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat()
        }
    )