from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text, or_
from typing import Annotated

from schemas import LangOpsProductResponse, LangOpsProductError, CheckHealthResponse
from models import LangOpsProductORM, orm_to_langops_product
from enums import MediaGroups, ProductCodes
from db import get_db

app = FastAPI()

@app.get("/api/health", response_model=CheckHealthResponse)
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
    


# Can return all LangOps products up to a limit of 500 per request.
# Will add filtering as required
# TODO: Add offset and anything else needed for pagination
@app.get(
        "/api/products", 
        response_model=list[LangOpsProductResponse], 
        responses={
            400: { "model": LangOpsProductError, "response_description": "Bad request" },
            404: { "model": LangOpsProductError, "response_description": "Record not found" },
            500: { "model": LangOpsProductError, "response_description": "Internal server error" }
            }
        )
async def get_all_products(
    language: Annotated[str | None, Query(description="The target language of the product in ISO-639-1 format")] = None,
    date_from: Annotated[datetime | None, Query(description="Date the product was published")] = None,
    date_to: Annotated[datetime | None, Query(description="Date the product was published")] = None,
    product_code: Annotated[ProductCodes | None, Query(description="The prefixed code indicating type of product, e.g. 'PT'")] = None, 
    media_groups: Annotated[list[MediaGroups] | None, Query(description="The general category of the product, e.g. website")] = None, 
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
    published_only: Annotated[bool, Query(description="Whether to return only products where date published is not null")] = False, 
    db: AsyncSession = Depends(get_db)
    ):
    if limit > 500 or limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 500.")
    
    statement = select(LangOpsProductORM).limit(limit)

    if language:
        statement = statement.where(LangOpsProductORM.trello_target_language == language)

    if product_code:
        statement = statement.where(LangOpsProductORM.trello_product_code == product_code)
    
    if date_from and date_to:
        statement = statement.where(LangOpsProductORM.trello_date_published.between(date_from, date_to))
    
    if media_groups:
       values = [g.value for g in media_groups]
       statement = statement.where(
           or_(*[LangOpsProductORM.trello_media_groups.any(v) for v in values])
        )
    
    if published_only:
        statement = statement.where(LangOpsProductORM.trello_date_published.is_not(None))
    
    result = await db.execute(statement)
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(status_code=404, detail="No records found")
    
    return [orm_to_langops_product(r) for r in rows]





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