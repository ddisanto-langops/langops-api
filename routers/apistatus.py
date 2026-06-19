from fastapi import APIRouter, Depends
from sqlalchemy import  text
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.response_schemas import CheckHealthResponse



router = APIRouter()


@router.get(
    "/api/v1/health",
    response_model=CheckHealthResponse
)
async def check_health(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(text("SELECT version();"))
    db_version = result.scalar()
    return CheckHealthResponse(
        database_version=db_version
    )
      

       