from fastapi import FastAPI, HTTPException, Depends
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

from schemas import LangOpsProductResponse, CheckHealthResponse
from models import LangOpsProductORM, orm_to_langops_product
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
    


@app.get("/api/products", response_model=list[LangOpsProductResponse])
async def get_all_products(db: AsyncSession = Depends(get_db)):
    statement = select(LangOpsProductORM)
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