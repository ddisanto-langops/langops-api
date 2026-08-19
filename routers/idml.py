from typing import Annotated
from fastapi import HTTPException, APIRouter, status, Body, Query

from schemas.error_schemas import ErrorResponses
from schemas.response_schemas import GetStringMapResponse
from schemas.data_schemas import StringMapItem
from functions import create_string_map, label_idml_strings

router = APIRouter()


@router.get(
    "/map",
    description="Returns JSON containing the context identifier, string IDs and strings of each XML story file from a specified IDML file. Intended to facilitate labeling of strings for translation assignments. Note that stories with less than 10 strings will be automatically labelled as 'miscellaneous' and will not be returned to the caller.",
    response_model=GetStringMapResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR,
        status.HTTP_502_BAD_GATEWAY: ErrorResponses._502_BAD_GATEWAY
    }
)
def get_string_map(
    crowdin_project_id: Annotated[int, Query(
        title="Crowdin project ID",
        alias="projectId",
        description="The numeric ID of the Crowdin project containing the IDML file (can be found on Crowdin 'dashboard' tab)"
    )],
    crowdin_file_id: Annotated[int, Query(
        title="Crowdin file ID",
        alias="fileId",
        description="The numeric ID of the desired IDML file in Crowdin (can be found in file URL)"
    )]
):
    try:
        string_map = create_string_map(crowdin_project_id, crowdin_file_id)
    
        return GetStringMapResponse(
            data=string_map
        )
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@router.post(
    "/label/{crowdin_project_id}",
    description="Label articles of an IDML file in Crowdin. Expects the 'label_id' property of the schema to be filled in by the caller.",
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
def label_idml(
    crowdin_project_id: int,
    schema: Annotated[list[StringMapItem], Body(
        title="String Map Schema",
        description="An object linking string IDs to a label title. See readme for more information."
    )]
):
    try:
        label_idml_strings(crowdin_project_id, schema)
        return status.HTTP_201_CREATED
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise Exception(e)