from typing import Annotated
from fastapi import APIRouter, status, Body

from schemas.error_schemas import ErrorResponses
from schemas.response_schemas import GetStringMapResponse
from schemas.data_schemas import StringMapItem
from functions import create_string_map, label_misc_strings, label_idml_strings

router = APIRouter()


@router.get(
    "/map/{crowdin_project_id}/{crowdin_file_id}",
    description="Get the context identifier, string IDs and text of each IDML story file to facilitate labeling, e.g. via a frontend service. Stories with less than 10 strings will be automatically labelled as miscellaneous and will not be shown to the caller.",
    response_model=GetStringMapResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
def get_string_map(
    crowdin_project_id: int,
    crowdin_file_id: int
):
    string_map = create_string_map(crowdin_project_id, crowdin_file_id)
    
    return GetStringMapResponse(
        data=string_map
    )


@router.post(
    "/label/{crowdin_project_id}",
    description="Label articles and miscellaneous strings of an .idml file in Crowdin. Requires the `label_id` property of the schema to be filled in by the caller.",
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
        description="A string map schema with string IDs as array and desired label as text. See readme for more information."
    )]
):
    label_idml_strings(crowdin_project_id, schema)



    



