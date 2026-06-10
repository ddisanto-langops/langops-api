from fastapi import FastAPI, HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text

app = FastAPI()

@app.get("/api/health")
def check_health():
    return {"status": "OK"}

@app.get("/api/products")
def get_all_products():
    sql = text(
        """
            SELECT 
                id,
                provenance,
                title,
                product_code,
                target_language AS "targetLanguage",
                product_status AS "productStatus",
                crowdin_url AS "crowdinUrl",
                trello_url AS "trelloUrl",
                article_url AS "articleUrl",
                editor_url AS "editorUrl",
                due_date AS "dueDate",
                date_last_activity AS "dateLastActivity",
                date_published AS "datePublished",
                translation_progress AS "translationProgress",
                approval_progress AS "approvalProgress",
                media_groups AS "mediaGroups",
                wordcount AS "wordCount"
            FROM products
            ORDER BY date_last_activity DESC NULLS LAST
        """
    )



@app.exception_handler(StarletteHTTPException)
def general_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An unknown error occurred."
    )
    return JSONResponse(
        status_code=exception.status_code,
        content={"detail": message}
    )