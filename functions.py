from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Any
import json

from models import IdmlStorageORM

async def get_idml_record(id: UUID, db: AsyncSession) -> IdmlStorageORM | None:
    """
    Args:
        id: the ID to target
        db: the LangOps IDML database
    """
    try:
        statement = select(IdmlStorageORM).where(IdmlStorageORM.id == id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get record: {e}")



def normalize_crowdin_file_ids(raw: Any) -> list[int]:
    if raw is None:
        return []

    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                items = parsed
            else:
                items = [part for part in text.split(",") if part.strip()]
        except json.JSONDecodeError:
            items = [part for part in text.split(",") if part.strip()]
    else:
        raise HTTPException(status_code=422, detail="Invalid crowdin_file_ids format")

    normalized: list[int] = []
    for item in items:
        if isinstance(item, str):
            item = item.strip().strip("[]").strip('"').strip("'")
            if item == "":
                continue
        try:
            normalized.append(int(item))
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="crowdin_file_ids must contain integers")
    return normalized