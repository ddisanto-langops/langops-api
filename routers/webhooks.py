from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends, Query, Body
from sqlalchemy import desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Annotated
from pydantic import ValidationError
from schemas.data_schemas import WebhookFailure, NewWebhookFailure
from schemas.error_schemas import ErrorResponses
from models import WebhookFailureORM, webhook_failure_orm_to_response
from db import get_db


router = APIRouter()

@router.get(
        "/failures",
        description="Get status and content for webhooks which were logged as failed",
        response_model=list[WebhookFailure],
        responses={
            status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
        }
)
async def get_failed_webhooks(
    limit: Annotated[int, Query(
        title="Limit",
        alias="limit",
        ge=1,
        le=500
    )] = 500,
    offset: Annotated[int, Query(
        title="Offset",
        alias="offset",
        description="Number of records to skip",
        ge=0
    )] = 0,
    db: AsyncSession = Depends(get_db)
):
    if limit > 500 or limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 500.")

    try:
        statement = select(WebhookFailureORM).limit(limit).offset(offset).order_by(desc(WebhookFailureORM.date_created))
        result = await db.execute(statement)
        rows = result.scalars().all()
        
        if not rows:
            raise HTTPException(status_code=404, detail="No records found")

        return [webhook_failure_orm_to_response(row) for row in rows]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e
        )



@router.post(
        "/failures",
        description="Log the status code text and raw JSON of webhooks which were rejected by this API, e.g. on creation or edit, to enable manual processing.",
        status_code=201,
        responses={
            status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
        }
)
async def log_webhook_failure(
    payload: Annotated[NewWebhookFailure, Body(description="The webhook payload wrapped in a WebhookFailure class")],
    db: AsyncSession = Depends(get_db)
):
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error logging webhook failure: must provide a payload"
        )
    try:
        db.add(WebhookFailureORM(
            date_created=datetime.now(timezone.utc),
            status_code=payload.status_code if payload else None,
            data=payload.data
        ))
        await db.commit()
        return status.HTTP_201_CREATED

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=e
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error logging webhook failure: {e}"
        )



@router.delete(
    "/failures/delete/{id}",
    description="Permanently delete the record of a failed webhook",
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def delete_failed_webhook(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    statement = delete(WebhookFailureORM).where(WebhookFailureORM.id == id).returning(WebhookFailureORM.id)
    result = await db.execute(statement)
    await db.commit()
        
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Unable to permanently delete product: not found")

    return {"status": "success", "id": id}