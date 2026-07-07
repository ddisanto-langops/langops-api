#
# WARNING: CONTAINS PLACEHOLDERS FOR TESTING
#

import os
import re
from datetime import datetime
from re import Match
from collections import defaultdict
from crowdin_api import CrowdinClient
from fastapi import HTTPException, status

from schemas.data_schemas import StringMapItem, StringMapPayload, NewLangOpsProduct, TrelloData, CrowdinData, YouTubeData
from schemas.request_schemas import AddProductRequest
from enums import CustomFields, ProductCodes, Languages, MediaGroups, ProductStatus, CROWDIN_PROJECT_IDS

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



def build_new_langops_products(products: list[AddProductRequest]) -> list[NewLangOpsProduct]:
    
    wordcount_pattern =                 r"(?<=-)(?:[A-Z+]*)([0-9]{1,})(?=_)"
    product_code_pattern =              r"^([A-Z-]*)([0-9]*[A-Z]*)(?=_)"
    magazine_pattern =                  r"^[A-Z]{2}([0-9]{6})_([A-Z]{2}-[A-Z]{2}$)"
    target_lang_pattern =               r"[A-Z]{2}$"
    editor_pattern =                    r"\/editor\/articles\/posts/"
    article_pattern =                   r"(?<!editor)\/articles\/posts"
    crowdin_link_pattern =              r"editor\/([A-z]{4,})\/([0-9]{5})"
    crowdin_project_and_file_pattern =  r"/editor/([a-z]{1,})"
    youTube_link_pattern =              r"youtube"

    langops_products: list[NewLangOpsProduct] = []

    for product in products:
        if not product.trello_data or not product.youtube_data or not product.crowdin_data:
            raise Exception({"error":"Missing one or more required data payloads"})
        

        name = product.trello_data.name

        if product.trello_data.custom_field_items:
            custom_fields = product.trello_data.custom_field_items
            for item in custom_fields:
                if item.id_custom_field == CustomFields.exclude and item.value.checked:
                    exclude = True
                else:
                    exclude = False
        
        product_code_match = re.search(product_code_pattern, name)
        if product_code_match:
            product_code = product_code_match[1]
        
        target_language_match = re.search(target_lang_pattern, name)
        if target_language_match:
            target_language = target_language_match[0]
        
        is_template = product.trello_data.is_template

        
        # Core filtering logic
        # Do not create product if:
        # 1. Has no product code or product code isn't valid;
        # 2. Is a template;
        # 3. "Exclude" is checked in custom fields;
        # 4. Target language missing or unsupported

        if not product_code or product_code not in {code.value for code in ProductCodes}:
            print(f"Skipped: {name} | Reason: Product code invalid or not yet supported (got {product_code})")
            continue
        elif is_template:
            print(f"Skipped: {name} | Reason: Card is a template")
        elif exclude:
            print(f"Skipped: {name} | Reason: 'Exclude' box is checked")
        elif not target_language or target_language not in {lang.value for lang in Languages}:
            print(f"Skipped: {name} | Reason: Target language missing or not yet supported (got {target_language})")
        else:
            print(f"Accepted: {name}")


        # Proceed to get the rest of the Trello data

        if product.trello_data.actions:
            actions = product.trello_data.actions
            for action in actions:
                if action.type == "updateCheckItemStateOnCard" and "[published]" in action.data.check_item.name.lower() and action.data.check_item.state == "complete":
                    date_published = action.date
                else: date_published = None

        wordcount_match = re.search(wordcount_pattern, name)
        if wordcount_match:
            wordcount = wordcount_match[1]
        
        if product.trello_data.attachments:
            attachments = product.trello_data.attachments
            for attachment in attachments:
                url = attachment.url
                
                editor_match = re.search(editor_pattern, url)
                if editor_match:
                    editor_url = url
                
                article_match = re.search(article_pattern, url)
                if article_match:
                    article_url = url
                    
                crowdin_match = re.search(crowdin_link_pattern, url)
                if crowdin_match:
                    crowdin_url = url
                
                youtube_match = re.search(youTube_link_pattern, url)
                if youtube_match:
                    youtube_url = url


        magazine = re.search(magazine_pattern, name)

        media_groups = []
        match product_code:
            case  "AD" | "LIT-S" | "MB" | "TB" | "TE":
                media_groups.append(MediaGroups.WEBSITE)
            
            case "ANN" | "BS" | "SER" | "SMT":
                media_groups.append(MediaGroups.INTERPRETATION)

            case "BCC" | "CWL" | "LIT":
                media_groups.append(MediaGroups.LITERATURE)
            
            case "LT":
                media_groups.append(MediaGroups.AUDIO_VIDEO, MediaGroups.WEBSITE)

            case "PCD" | "PN":
                media_groups.append(MediaGroups.EMAILS)
            
            case "KOD":
                if article_url:
                    media_groups.append(MediaGroups.AUDIO_VIDEO, MediaGroups.WEBSITE)
                else:
                    media_groups.append(MediaGroups.AUDIO_VIDEO)
            
            case "OTHER":
                if youtube_url:
                    media_groups.append(MediaGroups.AUDIO_VIDEO)
                else:
                    media_groups.append(MediaGroups.OTHER)
            
            case "POD" | "PTVID":
                if youtube_url:
                    media_groups.append(MediaGroups.AUDIO_VIDEO, MediaGroups.WEBSITE)
                else:
                    media_groups.append(MediaGroups.WEBSITE)
            
            case "PT" | "LS" | "RV":
                if magazine:
                    media_groups.append(MediaGroups.MAGAZINES)
                else:
                    media_groups.append(MediaGroups.WEBSITE)
            

        if crowdin_url:
            match: Match | None = re.search(crowdin_project_and_file_pattern, crowdin_url)
            if match:
                crowdin_project_name = match.group(1)
                crowdin_file_id = match.group(2)

                crowdin_project_id = CROWDIN_PROJECT_IDS.get(crowdin_project_name)


        # Product status
        if date_published:
            status = ProductStatus.PUBLISHED
        elif not date_published:
            client = create_crowdin_client(token=os.getenv("CROWDIN_API_TOKEN"))
            r = client.translation_status.get_file_progress(
                fileId=int(crowdin_file_id),
                projectId=int(crowdin_project_id)
            )
            for item in r['data'][0]:
                translation_progress = item['translationProgress']
                approval_progress = item['approvalProgress']
            
            if translation_progress and approval_progress:
                status = ProductStatus.PENDING
            else:
                status = ProductStatus.UNKNOWN
        else:
            status = ProductStatus.UNKNOWN
            

        
        


        trello_data = TrelloData(
            id=product.trello_data.id,
            url=product.trello_data.url,
            title=name,
            product_code=product_code,
            target_language=target_language,
            due_date=product.trello_data.due,
            date_published=date_published,
            date_last_activity=product.trello_data.date_last_activity,
            date_archived=product.trello_data.date_closed,
            word_count=wordcount,
            editor_url= editor_url or None,
            article_url= article_url or None,         
        )

        crowdin_data = CrowdinData(
            crowdin_file_id=crowdin_file_id or None,
            crowdin_project_id=crowdin_project_id or None,
            crowdin_url=crowdin_url or None
        )

        youtube_data = YouTubeData(
            url=youtube_url or None,

        )

        langops_products.append(
            NewLangOpsProduct(
                date_created= datetime.now(),
                date_deleted=None,
                media_groups=media_groups,
                product_status= status,
                trello_data=trello_data,
                youtube_data=youtube_data,
                crowdin_data=crowdin_data
            )
        )
    
    return langops_products