from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text, or_
from typing import Annotated

from schemas import LangOpsProductResponse, LangOpsProductError, CheckHealthResponse
from models import LangOpsProductORM, orm_to_langops_product
from enums import MediaGroupEnum, ProductCodeEnum, SupportedLanguageEnum
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
    except HTTPException as e:
        raise HTTPException(status_code=500, detail="Unable to get Postgres version: check that database is online.")
    

# GET: /api/products 
# is a simple endpoint to return all LangOps products. 
# Limited to max 500 per request.
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
    target_language: Annotated[SupportedLanguageEnum | None, Query()] = None,
    date_from: datetime = None, 
    date_to: datetime = None,
    product_code: Annotated[ProductCodeEnum | None, Query()] = None, 
    media_groups: Annotated[list[MediaGroupEnum] | None, Query()] = None, 
    limit: int = 500, 
    db: AsyncSession = Depends(get_db)
    ):
    if limit > 500 or limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 500.")
    
    statement = select(LangOpsProductORM).limit(limit)

    if target_language:
        statement = statement.where(LangOpsProductORM.trello_target_language == target_language)

    if product_code:
        statement = statement.where(LangOpsProductORM.trello_product_code == product_code)
    
    if date_from and date_to:
        statement = statement.where(LangOpsProductORM.trello_date_published.between(date_from, date_to))
    
    if media_groups:
       values = [g.value for g in media_groups]
       statement = statement.where(
           or_(*[LangOpsProductORM.trello_media_groups.any(v) for v in values])
        )
    
    result = await db.execute(statement)
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(status_code=404, detail="No records found")
    
    return [orm_to_langops_product(r) for r in rows]



@app.exception_handler(StarletteHTTPException)
def general_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An unknown error occurred."
    )
    return JSONResponse(
        status_code=exception.status_code,
        content={"detail": message}
    )