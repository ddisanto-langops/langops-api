from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends, Query, Path, Body
from sqlalchemy import asc, func, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from typing import Annotated

from schemas.response_schemas import (
    AddProductResponse,
    EditProductResponse,
    DeleteProductResponse,
    RestoreProductResponse,
    PaginatedProductResponse,  
    WordcountResponse, 
    ProductCodeCountResponse
) 

from schemas.data_schemas import (
    LangOpsProduct,
    NewLangOpsProduct,
    EditingLangOpsProduct,
    RawTrelloCard,
    ProductCodeCount
)
from schemas.error_schemas import ErrorResponses
from models import LangOpsProductORM, orm_to_langops_product, new_product_to_orm
from enums import MediaGroups, ProductCodes, ProductStatus
from constants import PRODUCT_CODE_MAX_LEN
from db import get_db
from functions import build_new_langops_products

router = APIRouter()



@router.get(
    "", 
    response_model=PaginatedProductResponse, 
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        
        status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def get_products(
    language: Annotated[str | None, Query(
        title="Target Language", 
        alias="targetLanguage", 
        description="The target language of the products in ISO-639-1 format",
        min_length=2,
        max_length=2
    )] = None,
    date_from: Annotated[datetime | None, Query(
        title="Date From", 
        alias="dateFrom", 
        description="Return products published on or after this date"
    )] = None,
    date_to: Annotated[datetime | None, Query(
        title="Date To", 
        alias="dateTo", 
        description="Return products published on or before this date"
    )] = None,
    product_code: Annotated[ProductCodes | None, Query(
        title="Product Code",
        alias="productCode",
        description="The prefixed code indicating type of product, e.g. 'PT'",
        max_length=PRODUCT_CODE_MAX_LEN
    )] = None, 
    media_groups: Annotated[list[MediaGroups] | None, Query(
        title="Media Groups",
        alias="mediaGroups",
        description="The general category of the product, e.g. website"
    )] = None, 
    search: Annotated[str | None, Query(
        title="Search",
        alias="search",
        description="Search for products by title or localized title"
    )] = None,
    limit: Annotated[int, Query(
        title="Limit",
        alias="limit",
        ge=1,
        le=500
    )] = 500,
    offset: Annotated[int, Query(
         title="Offset",
         alias="offset",
        description="Number of records to skip",
        ge=0
    )] = 0,
    archived_only: Annotated[bool, Query(
        title="Archived Only",
        alias="archivedOnly",
        description="Return only products which are archived in Trello"
    )] = False,
    published_only: Annotated[bool, Query(
        title="Published Only",
        alias="publishedOnly",
        description="""Whether to return only products where `date_published` **is not null.**
        <span style="color:red">If set to true, `unpublished_only` must be set to false.</span>"""
    )] = False,
    unpublished_only: Annotated[bool, Query(
        title="Unpublished Only",
        alias="unpublishedOnly",
        description="""Whether to return only products where `date_published` **is null.**
        <span style="color:red">If set to true, `published_only` must be set to false.</span>"""
    )] = False,
    exclude_deleted: Annotated[bool, Query(
        title="Exclude Deleted",
        alias="excludeDeleted",
        description="""Whether to exclude deleted products 
        (where date deleted is not null). If set to false, 
        deleted products will be returned along with active ones.
        """
    )] = True,
    db: AsyncSession = Depends(get_db)
    ):
    if limit > 500 or limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 500.")
    
    
    # Default behavior: select all products within limit and offset, order ascending.
    # NOTE: Excludes deleted products by default, unless exclude_deleted is set to True
    statement = (
        select(LangOpsProductORM)
        .order_by(asc(LangOpsProductORM.date_created))
        .limit(limit)
        .offset(offset)
    )

    if language:
        statement = statement.where(LangOpsProductORM.trello_target_language == language)

    if product_code:
        statement = statement.where(LangOpsProductORM.trello_product_code == product_code)  
    
    if date_from and date_to:
        statement = statement.where(LangOpsProductORM.trello_date_published.between(date_from, date_to))
    
    if media_groups:
        values = [g.value for g in media_groups]
        statement = statement.where(
            or_(*[LangOpsProductORM.media_groups.any(v) for v in values])
        )
    
    if search:
        search_filter = f"%{search}%"
        statement = statement.where(
            or_(
                LangOpsProductORM.trello_title.ilike(search_filter),
                LangOpsProductORM.trello_localized_title.ilike(search_filter)
            )
        )

    if archived_only:
        statement = statement.where(LangOpsProductORM.trello_date_archived.is_not(None))
    
    if published_only:
        statement = statement.where(LangOpsProductORM.trello_date_published.is_not(None))
    
    if unpublished_only:
        statement = statement.where(LangOpsProductORM.trello_date_published.is_(None))

    if exclude_deleted:
        statement = statement.where(LangOpsProductORM.date_deleted.is_(None))
    
    result = await db.execute(statement)
    rows = result.scalars().all()
    count = len(rows)

    if not rows:
        raise HTTPException(status_code=404, detail="No records found")
    

    return PaginatedProductResponse(
        total=count,
        offset=offset,
        limit=limit,
        data=[orm_to_langops_product(r) for r in rows]
    )


@router.get(
        "/wordcount",
        description="""Gets the sum of all word counts in LangOps products, 
        for published products only. Ignores unpublished and deletions.""",
        response_model=WordcountResponse,
        responses={
            status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
        }
)
async def get_word_count(
    language: Annotated[str | None, Query(
        title="Target Language", 
        alias="targetLanguage", 
        description="The target language of the products in ISO-639-1 format"
    )] = None,
    date_from: Annotated[datetime | None, Query(
        title="Date From", 
        alias="dateFrom", 
        description="Return products published on or after this date"
    )] = None,
    date_to: Annotated[datetime | None, Query(
        title="Date To", 
        alias="dateTo", 
        description="Return products published on or before this date"
    )] = None,
    product_code: Annotated[ProductCodes | None, Query(
        title="Product Code",
        alias="productCode",
        description="The prefixed code indicating type of product, e.g. 'PT'",
        max_length=PRODUCT_CODE_MAX_LEN
    )] = None, 
    media_groups: Annotated[list[MediaGroups] | None, Query(
        title="Media Groups",
        alias="mediaGroups",
        description="The general category of the product, e.g. website"
    )] = None, 
    db: AsyncSession = Depends(get_db)
):
    statement = (
        select(
            func.coalesce(func.sum(LangOpsProductORM.trello_word_count), 0)
        )
        .where(LangOpsProductORM.trello_word_count.is_not(None))
        .where(LangOpsProductORM.trello_date_published.is_not(None))
        .where(LangOpsProductORM.date_deleted.is_(None))
    )

    if language:
        statement = statement.where(LangOpsProductORM.trello_target_language == language)
    
    if date_from and date_to:
        statement = statement.where(LangOpsProductORM.trello_date_published.between(date_from, date_to))
    
    if product_code:
        statement = statement.where(LangOpsProductORM.trello_product_code == product_code)
    
    if media_groups:
        values = [g.value for g in media_groups]
        statement = statement.where(
            or_(*[LangOpsProductORM.media_groups.any(v) for v in values])
        )
    

    total_words = await db.scalar(statement)

    return WordcountResponse(
        total_words=total_words
    )


@router.get(
        "/productcount",
        description="Gets the count of each product code in LangOps products for published products only. Ignores unpublished and deletions.",
        response_model=ProductCodeCountResponse,
        responses={
            status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
        }
)
async def get_product_count(
    language: Annotated[str | None, Query(
        title="Target Language", 
        alias="targetLanguage", 
        description="The target language of the products in ISO-639-1 format"
    )] = None,
    date_from: Annotated[datetime | None, Query(
        title="Date From", 
        alias="dateFrom", 
        description="Return products published on or after this date"
    )] = None,
    date_to: Annotated[datetime | None, Query(
        title="Date To", 
        alias="dateTo", 
        description="Return products published on or before this date"
    )] = None,
    product_code: Annotated[ProductCodes | None, Query(
        title="Product Code",
        alias="productCode",
        description="The prefixed code indicating type of product, e.g. 'PT'",
        max_length=PRODUCT_CODE_MAX_LEN
    )] = None, 
    media_groups: Annotated[list[MediaGroups] | None, Query(
        title="Media Groups",
        alias="mediaGroups",
        description="The general category of the product, e.g. website"
    )] = None, 
    db: AsyncSession = Depends(get_db)
):
    filters = [
        LangOpsProductORM.trello_product_code.is_not(None),
        LangOpsProductORM.trello_date_published.is_not(None),
        LangOpsProductORM.date_deleted.is_(None),
    ]

    if language:
        filters.append(LangOpsProductORM.trello_target_language == language)
    
    if date_from and date_to:
        filters.append(LangOpsProductORM.trello_date_published.between(date_from, date_to))
    
    if product_code:
        filters.append(LangOpsProductORM.trello_product_code == product_code)
    
    if media_groups:
        values = [g.value for g in media_groups]
        filters.append(or_(*[LangOpsProductORM.media_groups.any(v) for v in values]))
    
    total_statement = select(func.count(LangOpsProductORM.trello_product_code)).where(*filters)

    grouped_statement = (
        select(
            LangOpsProductORM.trello_product_code.label("product_code"),
            func.count().label("count")
        )
        .where(*filters)
        .group_by(LangOpsProductORM.trello_product_code)
        .order_by(LangOpsProductORM.trello_product_code.asc())
    )
    
    total_products = await db.scalar(total_statement)
    grouped_result = await db.execute(grouped_statement)
    rows = grouped_result.all()

    return ProductCodeCountResponse(
        total_products=total_products or 0,
        data=[
            ProductCodeCount(product_code=row.product_code, count=row.count) for row in rows
        ]
    )


@router.get(
    "/{id}",
    description="Get a product by its unique ID",
    response_model=LangOpsProduct,
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def get_product_by_id(
    id: Annotated[str, Path(description="The unique Trello ID of the product)")],
    db: AsyncSession = Depends(get_db)
):
    statement = select(LangOpsProductORM).where(LangOpsProductORM.trello_id == id)
    result = await db.execute(statement)
    row = result.scalars().one_or_none()

    return orm_to_langops_product(row)


@router.post(
    "/add",
    description="Endpoint for LangOps Gateway to add a product or multiple products to the database. <span style='color:red'>To avoid duplicates and unpredictable behavior, end users are not allowed to add products directly. All add product requests should be handled via the source of truth.</span>",
    response_model=AddProductResponse,
    status_code=201,
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def add_product(
    products: Annotated[list[RawTrelloCard], Body(description="The combined, extracted JSON from each service which is to be evaluated in order to create a product or products")],
    db: AsyncSession = Depends(get_db)      
):  
    new_products = build_new_langops_products(products)
    if not new_products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add product: validation failed"
        )
    
    db.add_all([new_product_to_orm(product) for product in new_products])
    await db.commit()
    
    return AddProductResponse(
        total_products_added= len(new_products),
        data=new_products
    )



@router.post(
    "/user-add",
    description="Endpoint to manually add a LangOps product to the database, e.g. via a frontend. <span style='color:red'>Warning: This is a fully manual endpoint, which bypasses the product creation factory function. Use it only if you intend to manually add a product which was missed by automation.</span> **Note: as this bypasses the automation, the caller should consider supplying values which are normally created automatically.**",
    response_model=AddProductResponse,
    status_code=201,
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def user_add_product(
    product: Annotated[NewLangOpsProduct, Body()],
    db: AsyncSession = Depends(get_db)      
):  

    orm_product = LangOpsProductORM(**product.model_dump(exclude_none=False))
    db.add(orm_product)
    await db.commit()
    
    return AddProductResponse(
        total_products_added= 1,
        data=[product]
    )


@router.patch(
        "/edit/{id}",
        description="Edit an existing product",
        response_model=EditProductResponse,
        responses={
            status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
            status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
        }
)
async def edit_product(
    id: Annotated[str, Path(description="The unique Trello ID of the product to be edited)")],
    updated_data: Annotated[RawTrelloCard, Body()],
    db: AsyncSession = Depends(get_db)
):
    # ensure ID of product to edit corresponds to the one in RawTrelloCard body
    if updated_data.id != id:
        raise ValueError("Mismatch between requested Trello ID and Trello ID in updated product body field")
    
    # re-compute the LangOps product on edit, to ensure all dervied fields remain consistent with domain logic
    edited_product_list: list[LangOpsProduct] = build_new_langops_products([updated_data])
    if not edited_product_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Edit product: validation failed"
        )
    
    edited_product: LangOpsProductORM = new_product_to_orm(edited_product_list[0])
    
    statement = select(LangOpsProductORM.id).where(LangOpsProductORM.trello_id == id) # Get the actual LangOps UUID by referencing Trello ID
    result = await db.execute(statement)
    
    existing_id = result.scalar_one_or_none()
    if existing_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edit product: not found"
        )

    edited_product.id = existing_id # Fill in the LangOps UUID with the one derived from the DB
    merged = await db.merge(edited_product) 

    await db.commit()

    return EditProductResponse.model_validate(merged)

@router.patch(
        "/user-edit/{id}",
        description="Manually edit an existing product, e.g. via a frontend. <span style='color:red'>Warning: This is a fully manual endpoint, which bypasses the product creation factory function. Use it only if you intend to manually edit a product which was missed by automation.</span> **Note: as this bypasses the automation, the caller should consider supplying values which are normally created automatically.**",
        response_model=EditProductResponse,
        responses={
            status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
            status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
        }
)
async def user_edit_product(
    id: Annotated[str, Path(description="The unique Trello ID of the product to be edited")],
    product: Annotated[EditingLangOpsProduct, Body()],
    db: AsyncSession = Depends(get_db)
):
    statement = select(LangOpsProductORM).where(LangOpsProductORM.trello_id == id)
    result = await db.execute(statement)
    existing_product = result.scalar_one_or_none()

    if existing_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edit product: not found"
        )
    
    # Explicit mapping to determine what can or can't be edited
    existing_product.date_created = product.date_created
    existing_product.product_status = product.product_status
    existing_product.media_groups = product.media_groups

    existing_product.trello_id = product.trello_data.id
    existing_product.trello_url = str(product.trello_data.url)
    existing_product.trello_title = product.trello_data.title

    if product.trello_data.localized_title:
        existing_product.trello_localized_title = product.trello_data.localized_title

    existing_product.trello_product_code = product.trello_data.product_code
    existing_product.trello_target_language = product.trello_data.target_language
    
    if product.trello_data.due_date:
        existing_product.trello_due_date = product.trello_data.due_date

    if product.trello_data.date_published:
        existing_product.trello_date_published = product.trello_data.date_published
    
    existing_product.trello_date_last_activity = product.trello_data.date_last_activity
    if product.trello_data.date_archived:
        existing_product.trello_date_archived = product.trello_data.date_archived
    
    if product.trello_data.editor_url:
        existing_product.trello_editor_url = str(product.trello_data.editor_url)
    
    if product.trello_data.article_url:
        existing_product.trello_article_url = str(product.trello_data.article_url)
    
    if product.trello_data.word_count:
        existing_product.trello_word_count = product.trello_data.word_count

    if product.youtube_data:
        if product.youtube_data.id:
            existing_product.youtube_id = product.youtube_data.id
        
        if product.youtube_data.url:
            existing_product.youtube_url = str(product.youtube_data.url)

        if product.youtube_data.localized_title:
            existing_product.youtube_localized_title = product.youtube_data.localized_title

        if product.youtube_data.duration_seconds:
            existing_product.youtube_duration_seconds = product.youtube_data.duration_seconds

    if product.crowdin_data:
        if product.crowdin_data.crowdin_file_id:
            existing_product.crowdin_file_id = product.crowdin_data.crowdin_file_id
        
        if product.crowdin_data.crowdin_project_id:
            existing_product.crowdin_project_id = product.crowdin_data.crowdin_project_id
        
        if product.crowdin_data.translation_progress:
            existing_product.crowdin_translation_progress = product.crowdin_data.translation_progress
        
        if product.crowdin_data.approval_progress:
            existing_product.crowdin_approval_progress = product.crowdin_data.approval_progress
        
        if product.crowdin_data.crowdin_url:
            existing_product.crowdin_url = str(product.crowdin_data.crowdin_url)

    try:
        merged = await db.merge(existing_product)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Edit product: conflicting key"
        )

    await db.refresh(existing_product)
    return EditProductResponse.model_validate(merged)


@router.patch(
    "/restore/{id}",
    description="Restore a soft-deleted product",
    response_model=RestoreProductResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def restore_product(
    id: Annotated[str, Path(description="The product's Trello ID)")],
    db: AsyncSession = Depends(get_db)
):
    statement = (
        update(LangOpsProductORM)
            .where(LangOpsProductORM.trello_id == id)
            .values(date_deleted=None)
            .returning(LangOpsProductORM.trello_id)
        )
    result = await db.execute(statement)

    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.commit()

    return RestoreProductResponse(
        id=id,
        restored_at=datetime.now(timezone.utc)
    )


@router.delete(
    "/delete/{id}",
    description="Soft delete of a product",
    response_model=DeleteProductResponse, 
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def delete_product(
    id: Annotated[str, Path(description="The Trello ID of the product")],
    db: AsyncSession = Depends(get_db)
):
    timestamp = datetime.now(timezone.utc)
    statement = (
        update(LangOpsProductORM)
            .where(LangOpsProductORM.trello_id == id)
            .values(date_deleted=timestamp)
            .values(product_status=ProductStatus.DELETED)
            .returning(LangOpsProductORM.trello_id)
    )

    result = await db.execute(statement)
    

    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Unable to soft-delete product: not found")

    await db.commit()

    return DeleteProductResponse(
        id=id,
        deleted_at=timestamp
    )


@router.delete(
    "/permanent-delete/{id}",
    description="**Hard delete** of a product",
    response_model=DeleteProductResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: ErrorResponses._400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorResponses._401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ErrorResponses._422_VALIDATION_ERROR,
        status.HTTP_404_NOT_FOUND: ErrorResponses._404_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponses._500_INTERNAL_SERVER_ERROR
    }
)
async def permanently_delete_product(
    id: Annotated[str, Path(description="The unique ID of the product (not a Trello or Crowdin ID)")],
    db: AsyncSession = Depends(get_db)
):
    statement = delete(LangOpsProductORM).where(LangOpsProductORM.trello_id == id).returning(LangOpsProductORM.id)
    result = await db.execute(statement)
    await db.commit()

    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Unable to permanently delete product: not found")

    return DeleteProductResponse(
        id=id,
        deleted_at=datetime.now(timezone.utc)
    )