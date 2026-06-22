import os
import io
import asyncio
import httpx
from fastapi import APIRouter, HTTPException, status, Depends, File, Form, Path, UploadFile, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
from typing import Annotated
from uuid import UUID

from db import AsyncSession, get_db
from models import IdmlStorageORM
from schemas.response_schemas import (
    GetIDMLResponse,
    StoreIdmlResponse,
    ReconstructIDMLResponse
)
from schemas.error_schemas import ErrorResponses
from functions import get_idml_record, normalize_crowdin_file_ids

router = APIRouter()


@router.get(
    "/list",
    description="Lists the IDMLs present in the LangOps IDML storage table",
    response_model=list[GetIDMLResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def list_idmls(
    db: AsyncSession = Depends(get_db)
):

    statement = select(IdmlStorageORM)
    result = await db.execute(statement)
    rows = result.scalars().all()
    
    return rows



@router.get(
        "/{id}",
        description="Gets an IDML record from the IDML storage table by ID",
        response_model=GetIDMLResponse,
        responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def get_record(
    id: Annotated[UUID, Path(description="The unique ID of the product (not a Trello or Crowdin ID)")],
    db: AsyncSession = Depends(get_db)
):
    record = await get_idml_record(id, db)

    if record is None:
        raise HTTPException(status_code=404, detail="IDML record not found")

    return GetIDMLResponse(
        id=id,
        file_name=record.file_name,
        project=record.crowdin_project_name,
        target_language=record.target_language,
        crowdin_file_ids=normalize_crowdin_file_ids(record.crowdin_file_ids),
        status=record.status,
        date_created=record.created_at
    )


@router.get(
        "/download/{id}",
        description="Get download link for a reconstructed XLIFF",
        responses={
            status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
        }
)
async def download_reconstructed_file(
    id: Annotated[UUID, Path(description="Stored IDML record ID")], 
    db: AsyncSession = Depends(get_db)
):
    statement = select(IdmlStorageORM).where(IdmlStorageORM.id == id)
    result = await db.execute(statement)
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No reconstructed IDML found in database for this ID")

    raw_bytes = record.rebuilt_idml_data
    if not raw_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This database row exists, but its binary byte fields are empty")

    
    original_filename = record.file_name

    return StreamingResponse(
        io.BytesIO(raw_bytes),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{original_filename}.idml"'
        }
    )
    

@router.post(
    "/parse",
    description="""Sends an .idml file to be parsed into individual XLIFFs by the LangOps IDML handler service.
    This returns multiple XLIFF files which correspond to the stories inside the .idml file.""",
    response_class=Response,
    status_code=201,
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def parse_idml(
    file: UploadFile = File(title="IDML File", alias="idmlFile", description="The inDesign file to be parsed"),
    source_language: str = Form(default="en", title="Source Language", alias="sourceLanguage")
    
):
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="No file provided")

    cf_client_id = os.environ["IDML_CF_ACCESS_CLIENT_ID"]
    cf_client_secret = os.environ["IDML_CF_ACCESS_CLIENT_SECRET"]

    upstream = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: httpx.post(
            "https://idml.pcglangops.com/parse",
            headers={
                "CF-Access-Client-Id": cf_client_id,
                "CF-Access-Client-Secret": cf_client_secret
            },
            files={"idml": (file.filename, file_bytes, "application/octet-stream")},
            data={"source_lang": source_language},
            timeout=60.0,
        )
    )

    if not upstream.is_success:
        raise HTTPException(status_code=502, detail=f"Upstream Status {upstream.status_code}: {upstream.text}")

    return Response(
        status_code=201,
        content=upstream.content,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=parsed.zip"}
    )


@router.post(
    "/store",
    description="""Stores the parsed XLIFF files and original IDML
    in the LangOps IDML database for future reconstruction""",
    status_code=201,
    response_model=StoreIdmlResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def store_idml(
    idml_file: UploadFile = File(alias="idml"),
    xliff_zip: UploadFile = File(alias="xliffZip"),
    file_name: str = Form(alias="fileName"),
    crowdin_project_id: str = Form(alias="projectId"),
    crowdin_project_name: str = Form(alias="projectName"),
    target_language: str = Form(alias="targetLanguage"),
    crowdin_file_ids: str = Form(alias="crowdinFileIds"),
    db: AsyncSession = Depends(get_db)
):
    idml_bytes = await idml_file.read()
    zip_bytes = await xliff_zip.read()

    if not idml_bytes or not zip_bytes:
        raise HTTPException(status_code=400, detail="Both idml and xliffZip files are required")

    normalized_ids = normalize_crowdin_file_ids(crowdin_file_ids)
    if not normalized_ids:
        raise HTTPException(status_code=400, detail="crowdinFileIds must not be empty")

    record = IdmlStorageORM(
        file_name=file_name,
        idml_data=idml_bytes,
        xliff_zip_data=zip_bytes,
        crowdin_project_id=crowdin_project_id,
        crowdin_project_name=crowdin_project_name,
        target_language=target_language,
        crowdin_file_ids=normalized_ids,
        status="pending",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return {"id": record.id}




@router.post(
    "/reconstruct/{id}",
    description="""Reconstructs an IDML file from translated XLIFF files,
    via the LangOps IDML database.""",
    status_code=201,
    response_model=ReconstructIDMLResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def reconstruct_idml(
    id: Annotated[UUID, Path(description="Stored IDML record ID")],
    xliffs: UploadFile = File(description="ZIP archive of translated XLIFFs"),
    db: AsyncSession = Depends(get_db)
):
    record = await get_idml_record(id, db)
    if record is None:
        raise HTTPException(status_code=404, detail="IDML record not found")

    if not record.idml_data:
        raise HTTPException(status_code=422, detail="Stored IDML binary is missing")

    file_ids = normalize_crowdin_file_ids(record.crowdin_file_ids) if record.crowdin_file_ids else []

    cf_client_id = os.environ["IDML_CF_ACCESS_CLIENT_ID"]
    cf_client_secret = os.environ["IDML_CF_ACCESS_CLIENT_SECRET"]

    _idml_bytes = bytes(record.idml_data)
    _file_name = record.file_name
    _xliffs_bytes = await xliffs.read()

    try:
        upstream = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: httpx.post(
                "https://idml.pcglangops.com/reconstruct",
                headers={
                    "CF-Access-Client-Id": cf_client_id,
                    "CF-Access-Client-Secret": cf_client_secret
                },
                files=[
                    ("idml", (_file_name, _idml_bytes, "application/octet-stream")),
                    ("xliffs", (xliffs.filename or "xliff_out.zip", _xliffs_bytes, "application/zip")),
                ],
                timeout=90.0,
            )
        )

        if not upstream.is_success:
            record.status = "failed"
            await db.commit()
            raise HTTPException(
                status_code=502,
                detail=f"Upstream Status {upstream.status_code}: {upstream.text}"
            )

        rebuilt_content = upstream.content

        record.rebuilt_idml_data = rebuilt_content
        record.status = "completed"
        await db.commit()
        await db.refresh(record)

        return ReconstructIDMLResponse(
            id=record.id,
            file_name=record.file_name,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
            crowdin_file_ids=file_ids,
            crowdin_project_id=record.crowdin_project_id,
            target_language=record.target_language,
            rebuilt_available=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        record.status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Reconstruct failed: {e}")