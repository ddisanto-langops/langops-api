from fastapi import APIRouter, status, Depends, Header, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from schemas.error_schemas import ErrorResponses
from webhook_auth import TrelloWebhook

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
async def process_trello_webhook(
    request: Request,
    x_trello_webhook: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    trello_adapter = TrelloWebhook()

    raw_body = await request.body()

    if not x_trello_webhook:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Trello signature header"
        )

    if not trello_adapter.verify_signature(raw_body, x_trello_webhook):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid signature"
        )


    payload = await request.json()


    return {
        "status": "accepted"
    }
