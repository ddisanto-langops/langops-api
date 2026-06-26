#
# WARNING: CONTAINS PLACEHOLDERS FOR TESTING
#

import os
import re
from collections import defaultdict
from crowdin_api import CrowdinClient
from fastapi import HTTPException, status

from schemas.data_schemas import StringMapItem, StringMapPayload

def create_crowdin_client(token: str) -> CrowdinClient:
    return CrowdinClient(
        token=token,
        timeout=30,
        max_retries=2
    )



def create_string_map(
    crowdin_project_id: int,
    crowdin_file_id: int
) -> list[StringMapItem]:
    context_regex = r"(^[A-Z0-9]{1,})-"
    limit = 500
    offset = 0
    has_more = True

    grouped: dict[str, dict[str, list[int] | list[str] | None]] = defaultdict(
        lambda: {
            "ids": [],
            "strings": [],
            "label_id": None,
        }
    )

    token = os.getenv("CROWDIN_API_TOKEN")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CROWDIN_API_TOKEN is not configured.",
        )

    client = create_crowdin_client(token)

    try:
        res = client.source_strings.list_strings(
            projectId=int(crowdin_project_id),
            fileId=int(crowdin_file_id),
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve file strings from Crowdin.",
        ) from e

    res_length = len(res["data"])

    while res_length > 0 and has_more:
        for string in res["data"]:
            identifier = string["data"]["identifier"]
            context_match = re.search(context_regex, identifier)
            if not context_match:
                continue

            context = context_match.group(1)
            grouped[context]["ids"].append(string["data"]["id"])
            grouped[context]["strings"].append(string["data"]["text"])

        offset += res_length

        try:
            res = client.source_strings.list_strings(
                projectId=int(crowdin_project_id),
                fileId=int(crowdin_file_id),
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to retrieve additional file strings from Crowdin: {e}.",
            ) from e

        res_length = len(res["data"])
        if res_length < limit:
            has_more = False

    return [
        StringMapItem(
            context_identifier=context,
            map=StringMapPayload(
                string_ids=payload["ids"],
                strings=payload["strings"],
                label_id=payload["label_id"],
            ),
        )
        for context, payload in grouped.items()
    ]



def label_misc_strings(
        crowdin_project_id: int,
        string_data: list[StringMapItem],
    ) -> None:
    """
        If a context label has less than 10 strings, label it as miscellaneous.
        Only context labels which own 10 strings or more will be exposed to the user
        for labelling.
    """
    
    try:
        client = create_crowdin_client(token=os.getenv("CROWDIN_API_TOKEN"))
        client.labels.add_label(
            title="Miscellaneous",
            projectId=crowdin_project_id
        )
    except Exception as e:
        print(f"Error adding label. Check if label already exists. Message: {e}")

    misc_strings = []
    misc_strings_count = 0

    for item in string_data:
        if len(item.map.string_ids) < 10:
            for id in item.map.string_ids:
                misc_strings.append(int(id))
                misc_strings_count +=1

    try:
        client.labels.assign_label_to_strings(
            labelId=1412, # PLACEHOLDER FOR "Miscellaneous" LABEL
            stringIds=misc_strings,
            projectId=crowdin_project_id
        )

    except Exception as e:
        print(f"Failed to lable misc. strings: {e}")
            
    return {
        "status": "OK",
        "Misc. string count": misc_strings_count,
        "ids": misc_strings
    }


def label_idml_strings(
        crowdin_project_id: int, 
        labeled_string_data: list[StringMapItem]
    ) -> None:

    token = os.getenv("CROWDIN_API_TOKEN")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CROWDIN_API_TOKEN is not configured."
        )

    client = create_crowdin_client(token)

    for item in labeled_string_data:
        if not item.map.label_id:
            continue
        
        if len(item.map.string_ids) >= 10:
            client.labels.assign_label_to_strings(
                labelId=item.map.label_id,
                stringIds=item.map.string_ids,
                projectId=crowdin_project_id
            )