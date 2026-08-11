import os
import re
import requests
import logging
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup as Scraper
from datetime import datetime, timedelta, timezone
from re import Match
from collections import defaultdict
from crowdin_api import CrowdinClient
from fastapi import HTTPException, status

from schemas.data_schemas import (
    StringMapItem,
    StringMapPayload,
    RawTrelloCard,
    NewLangOpsProduct,
    TrelloData,
    CrowdinData,
    YouTubeData,
)       
from enums import CustomFields, ProductCodes, Languages, MediaGroups, ProductStatus, CROWDIN_PROJECT_IDS

logger = logging.getLogger("uvicorn.error")


def create_crowdin_client(token: str) -> CrowdinClient:
    return CrowdinClient(
        token=token,
        timeout=30,
        max_retries=2
    )



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

        label_id: int | None = None
        labels_res = client.labels.list_labels(
            projectId=crowdin_project_id
        )

        if labels_res:
            for item in labels_res['data']:
                title = item['data']['title'].lower()
                if title == "miscellaneous": # label exists
                    label_id = item['data']['id']
            
        if label_id is None:
            add_label_res = client.labels.add_label(
                title="miscellaneous",
                projectId=crowdin_project_id
            )
            label_id = add_label_res['data'][ 'id']

        if not label_id:
            raise Exception("Unable to find label ID for misc strings. Exiting process.")

    except Exception as e:
        print(f"Error creating misc. label in Crowdin: {e}")

    misc_strings = []
    misc_strings_count = 0

    for item in string_data:
        if len(item.map.string_ids) <= 10:
            for id in item.map.string_ids:
                misc_strings.append(int(id))
                misc_strings_count +=1

    try:
        client.labels.assign_label_to_strings(
            labelId=label_id,
            stringIds=misc_strings,
            projectId=crowdin_project_id
        )

    except Exception as e:
        print(f"Failed to lable misc. strings: {e}")
            
    return {
        "status": status.HTTP_201_CREATED,
        "Misc. string count": misc_strings_count,
        "ids": misc_strings
    }



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

    mapped_strings = [
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

    label_misc_strings(crowdin_project_id, mapped_strings)

    user_strings = []
    for item in mapped_strings:
        if len(item.map.strings) >= 10:
            user_strings.append(item)

    return user_strings



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
        label_id = None
        user_label = item.map.label_text or None
        if not user_label:
            continue
        else:
            try:
                labels_res = client.labels.list_labels(
                    projectId=crowdin_project_id
                )
                for crowdin_label in labels_res['data']:
                    title: str = crowdin_label['data']['title']
                    if title.lower() == user_label.lower(): # label exists
                        label_id = crowdin_label['data']['id']
                
                if label_id is None:
                    add_label_res = client.labels.add_label(
                        title=user_label,
                        projectId=crowdin_project_id
                    )
                    label_id = add_label_res['data'][ 'id']

            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to add label to Crowdin: {e}.",
                ) from e
            
        
        if len(item.map.string_ids) >= 10:
            client.labels.assign_label_to_strings(
                labelId=label_id,
                stringIds=item.map.string_ids,
                projectId=crowdin_project_id
            )



def get_localized_title(url: str):
    if not url:
        raise ValueError({"error": "URL for localized title cannot be null"})

    try:
        response = requests.get(url)
        response.raise_for_status()

        html = Scraper(response.text, "html.parser")
        title = html.find("h1").get_text()

        return title

    except HTTPError as e:
        logger.error(f"Error: unable to get localized title: {e}")

    

def build_new_langops_products(products: list[RawTrelloCard]) -> list[NewLangOpsProduct]:
    
    wordcount_pattern =                 r"(?<=-)(?:[A-Z+]*)([0-9]{1,})(?=_)"
    product_code_pattern =              r"^([A-Z-]*)([0-9]*[A-Z]*)(?=_)"
    magazine_pattern =                  r"^[A-Z]{2}([0-9]{6})_([A-Z-]{2,}$)"
    target_lang_pattern =               r"([A-Z]{2})$"
    editor_pattern =                    r"\/editor\/articles\/posts/"
    article_pattern =                   r"(?<!editor)\/articles\/posts"
    crowdin_link_pattern =              r"editor\/([A-z]{4,})\/([0-9]{5})"
    youTube_link_pattern =              r"youtube"

    langops_products: list[NewLangOpsProduct] = []

    for product in products:

        # get some intitial data to help with filtering
        name = product.name

        exclude = False
        if product.actions:
            actions = product.actions
            for action in actions:
                try:
                    action_id = action.data.custom_field_item.id_custom_field
                    checkbox = action.data.custom_field_item.value.checked
                    if action_id == CustomFields.exclude and checkbox and checkbox == 'true':
                        exclude = True
                except:
                    pass
                    

        
        product_code = None
        product_code_match: Match | None = re.search(product_code_pattern, name)
        if product_code_match:
            product_code = product_code_match.group(1)
        
        target_language = None
        target_language_match: Match | None = re.search(target_lang_pattern, name)
        if target_language_match:
            target_language: str = target_language_match.group(0).lower()
        
        is_template = product.is_template

        
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
            continue
        elif exclude:
            print(f"Skipped: {name} | Reason: 'Exclude' box is checked")
            continue
        elif not target_language or target_language not in {lang.value for lang in Languages}:
            print(f"Skipped: {name} | Reason: Target language missing or not yet supported (got {target_language})")
            continue
        else:
            print(f"Parsed product: {name}")


        # product is valid, apply the rest of the domain logic
        date_published = None
        if product.actions:
            actions = product.actions
            for action in actions:
                try:
                    action_id = action.data.custom_field_item.id_custom_field
                    checkbox = action.data.custom_field_item.value.checked
                    if action_id == CustomFields.published and checkbox and checkbox == 'true' :
                        date_published = action.date
                except:
                    pass

    
        wordcount = 0
        wordcount_match: Match | None = re.search(wordcount_pattern, name)
        if wordcount_match:
            wordcount = wordcount_match.group(1)
            
        editor_url: str | None = None
        article_url: str | None = None
        crowdin_url: str | None = None
        youtube_url: str | None = None
        if product.attachments:
            attachments = product.attachments
            for attachment in attachments:
                url = str(attachment.url) 
                
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

        if article_url:
            try:
                localized_title = get_localized_title(article_url)
            except Exception:
                localized_title = None
        else:
            localized_title = None

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
                media_groups.extend(MediaGroups.AUDIO_VIDEO, MediaGroups.WEBSITE)

            case "PCD" | "PN":
                media_groups.append(MediaGroups.EMAILS)
            
            case "KOD":
                if article_url:
                    media_groups.extend(MediaGroups.AUDIO_VIDEO, MediaGroups.WEBSITE)
                else:
                    media_groups.append(MediaGroups.AUDIO_VIDEO)
            
            case "OTHER":
                if youtube_url:
                    media_groups.append(MediaGroups.AUDIO_VIDEO)
                else:
                    media_groups.append(MediaGroups.OTHER)
            
            case "POD" | "PTVID":
                if youtube_url:
                    media_groups.extend(MediaGroups.AUDIO_VIDEO, MediaGroups.WEBSITE)
                else:
                    media_groups.append(MediaGroups.WEBSITE)
            
            case "PT" | "LS" | "RV":
                if magazine:
                    media_groups.append(MediaGroups.MAGAZINES)
                else:
                    media_groups.append(MediaGroups.WEBSITE)
        
        # If Crowdin editor URL, attempt to extract project name and file ID,
        # then correlate project name to its ID
        crowdin_file_id: int | None = None
        crowdin_project_id: int | None = None
        if crowdin_url:
            match: Match | None = re.search(crowdin_link_pattern, crowdin_url)
            if match:
                crowdin_project_name = match.group(1).lower()
                crowdin_file_id = int(match.group(2))
                crowdin_project_id = int(CROWDIN_PROJECT_IDS.get(crowdin_project_name))

        # Product status
        status = ProductStatus.UNKNOWN
        translation_progress = 0.0
        approval_progress = 0.0

        if product.date_closed:
            status = ProductStatus.ARCHIVED

        if date_published:
            status = ProductStatus.PUBLISHED
            translation_progress = 100.0
            approval_progress = 100.0
        elif crowdin_url and crowdin_file_id and crowdin_project_id:
            try:
                client = create_crowdin_client(token=os.getenv("CROWDIN_API_TOKEN"))
                r = client.translation_status.get_file_progress(
                    fileId=crowdin_file_id,
                    projectId=crowdin_project_id
                )
                crowdin_payload = r['data']

                for item in crowdin_payload:
                    translation_progress = item['data']['translationProgress']
                    approval_progress = item['data']['approvalProgress']
                
                    if translation_progress or approval_progress:
                        status = ProductStatus.PENDING
               
            except Exception as e:
                print(e)
        
        elif product.date_last_activity:
            last_activity = product.date_last_activity
            now = datetime.now(timezone.utc)
            if (last_activity + timedelta(days=7) >= now):
                status = ProductStatus.PENDING
        


        trello = TrelloData(
            id=product.id,
            url=product.url,
            title=name,
            localized_title=localized_title,
            product_code=product_code,
            target_language=target_language,
            due_date=product.due,
            date_published=date_published,
            date_last_activity=product.date_last_activity,
            date_archived=product.date_closed,
            word_count=wordcount or None,
            editor_url= editor_url or None,
            article_url= article_url or None,         
        )

        crowdin = CrowdinData(
            crowdin_file_id=crowdin_file_id or None,
            crowdin_project_id=crowdin_project_id or None,
            crowdin_url=crowdin_url or None,
            translation_progress=translation_progress,
            approval_progress=approval_progress
        )

        youtube = YouTubeData(
            url=youtube_url or None,
            id="",
            localized_title="",
            duration_seconds=0

        )

        langops_products.append(
            NewLangOpsProduct(
                date_created=datetime.now(),
                date_deleted=None,
                media_groups=media_groups,
                product_status=status,
                trello_data=trello,
                youtube_data=youtube,
                crowdin_data=crowdin
            )
        )

    return langops_products