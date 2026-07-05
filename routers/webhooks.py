from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.error_schemas import ErrorResponses

router = APIRouter()

@router.head(
    "/trello",
    responses={
        status.HTTP_405_METHOD_NOT_ALLOWED: ErrorResponses._405_METHOD_NOT_ALLOWED,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR,
    }
)
def connectivity_check():
    return status.HTTP_200_OK


@router.post(
    "/trello",
    responses={
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_405_METHOD_NOT_ALLOWED: ErrorResponses._405_METHOD_NOT_ALLOWED,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
def process_trello_webhook(
    json,
    db: AsyncSession = Depends(get_db)
):
    return {
        "status": "success"
    }