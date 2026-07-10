from fastapi import APIRouter, status, Depends
from sqlalchemy import  text
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.response_schemas import CheckHealthResponse
from schemas.error_schemas import ErrorResponses


router = APIRouter()


@router.head(
    "/",
    name="API Status",
    responses={
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
def api_status():
    return status.HTTP_200_OK


@router.get(
    "/database",
    response_model=CheckHealthResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def database_status(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(text("SELECT version();"))
    db_version = result.scalar()
    return CheckHealthResponse(
        database_version=db_version
    )
      

       