from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import IdmlStorageORM
from schemas.response_schemas import GetIDMLResponse

async def get_idml_record(id: int, db: AsyncSession) -> GetIDMLResponse:
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
        raise HTTPException(status_code=500, detail=f"Failted to get record: {e}")




async def mark_record_complete():
    """
    Marks a record as "completed" in the LangOps IDML database.

    """
    pass