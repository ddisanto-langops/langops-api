import os
import json
import httpx
from fastapi import APIRouter, HTTPException, Response, UploadFile, Depends, File, Form
from sqlalchemy.future import select

from db import AsyncSession, get_db
from models import IdmlStorageORM
from schemas import (
    GetIDMLResponse,
    StoreIdmlResponse,
    ReconstructIDMLResponse,
    ProductError
)
from functions import get_idml_record

router = APIRouter()


@router.get(
    "/api/idml/list",
    description="Lists the IDMLs present in the LangOps IDML storage table",
    response_model=list[GetIDMLResponse],
    responses={
        400: { "model": ProductError, "response_description": "Bad request" },
        404: { "model": ProductError, "response_description": "Record not found" },
        500: { "model": ProductError, "response_description": "Internal server error" }
    }
)
async def list_idmls(
    db: AsyncSession = Depends(get_db)
):
    try:
        statement = select(IdmlStorageORM)
        result = await db.execute(statement)
        rows = result.scalars().all()
        
        return [
            {
                "id": row.id,
                "file_name": row.file_name,
                "status": row.status,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            } 
            for row in rows
        ]
    
    except HTTPException:
        raise HTTPException(status_code=404, detail="No records found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to get IDML records: {e}")





@router.post(
    "/api/idml/parse",
    description="""Sends an .idml file to be parsed into individual XLIFFs by the LangOps IDML handler service.
    This returns multiple XLIFF files which correspond to the stories inside the .idml file.""",
    response_class=Response,
    status_code=201,
    responses={
        400: { "model": ProductError, "response_description": "Bad request" },
        500: { "model": ProductError, "response_description": "Internal server error" },
        502: { "model": ProductError, "response_description": "Upstream error" }
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
    "/api/idml/store",
    description="""Stores the parsed XLIFF files and original IDML
    in the LangOps IDML database for future reconstruction""",
    status_code=201,
    response_model=StoreIdmlResponse,
    responses={
        400: { "model": ProductError, "response_description": "Bad request" },
        500: { "model": ProductError, "response_description": "Internal server error" },
        502: { "model": ProductError, "response_description": "Upstream error" }
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
    try:
        parsed_ids = json.loads(crowdin_file_ids)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="crowdinFileIds must be a JSON array")

    idml_bytes = await idml_file.read()
    zip_bytes = await xliff_zip.read()

    if not idml_bytes or not zip_bytes:
        raise HTTPException(status_code=400, detail="Both idml and xliffZip files are required")

    try:
        record = IdmlStorageORM(
            file_name=file_name,
            idml_data=idml_bytes,
            xliff_zip_data=zip_bytes,
            crowdin_project_id=crowdin_project_id,
            crowdin_project_name=crowdin_project_name,
            target_language=target_language,
            crowdin_file_ids=parsed_ids,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return {"id": record.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store IDML record: {e}")




# TODO: Finish building reconstruct
@router.post(
    "/api/idml/reconstruct/{id}",
    description="""Reconstructs an IDML file from translated XLIFF files,
    via the LangOps IDML database.""",
    status_code=201,
    response_model=ReconstructIDMLResponse,
    responses={
        400: { "model": ProductError, "response_description": "Bad request" },
        500: { "model": ProductError, "response_description": "Internal server error" },
        502: { "model": ProductError, "response_description": "Upstream error" }
    }
)
async def reconstruct_idml(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        record = await get_idml_record(id, db)

        if record is None:
            raise HTTPException(status_code=404, detail="Record not found")
        


        return GetIDMLResponse(
            id=record.id,
            file_name=record.file_name,
            status=record.status,
            crowdin_file_ids=record.crowdin_file_ids
        )

    except HTTPException as e:
        raise HTTPException(status_code=500, detail=f"IDML reconstruct failed: {e}")