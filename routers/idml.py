import os
import httpx
from fastapi import APIRouter, HTTPException, status, Response, UploadFile, Depends, File, Form
from sqlalchemy.future import select

from db import AsyncSession, get_db
from models import IdmlStorageORM
from schemas.response_schemas import (
    GetIDMLResponse,
    StoreIdmlResponse,
    ReconstructIDMLResponse
)
from schemas.error_schemas import ErrorResponses
from functions import get_idml_record

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

    cf_client_id = os.environ["CF_ACCESS_CLIENT_ID"]
    cf_client_secret = os.environ["CF_ACCESS_CLIENT_SECRET"]

    async with httpx.AsyncClient(timeout=60.0) as client:
        upstream = await client.post(
            "https://idml.pcglangops.com/parse",
            headers={
                "CF-Access-Client-Id": cf_client_id,
                "CF-Access-Client-Secret": cf_client_secret
            },
            files={"idml": (file.filename, file_bytes, "application/octet-stream")},
            data={"source_lang": source_language}
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
    crowdin_project_id: str | None = Form(default=None, alias="projectId"),
    crowdin_project_name: str | None = Form(default=None, alias="projectName"),
    target_language: str | None = Form(default=None, alias="targetLanguage"),
    crowdin_file_ids: str = Form(default="[]", alias="crowdinFileIds"),
    db: AsyncSession = Depends(get_db)
):
    idml_bytes = await idml_file.read()
    zip_bytes = await xliff_zip.read()

    if not idml_bytes or not zip_bytes:
        raise HTTPException(status_code=400, detail="Both idml and xliffZip files are required")

    record = IdmlStorageORM(
        file_name=file_name,
        idml_data=idml_bytes,
        xliff_zip_data=zip_bytes,
        crowdin_project_id=crowdin_project_id,
        crowdin_project_name=crowdin_project_name,
        target_language=target_language,
        crowdin_file_ids=crowdin_file_ids,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return {"id": record.id}




# TODO: Finish building reconstruct
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
    id: int,
    db: AsyncSession = Depends(get_db)
):
    record = await get_idml_record(id, db)

    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    


    return GetIDMLResponse(
        id=record.id,
        file_name=record.file_name,
        status=record.status,
        crowdin_file_ids=record.crowdin_file_ids
    )