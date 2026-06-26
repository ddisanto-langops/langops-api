# LangOps API

LangOps API is a FastAPI service for translation operations at scale. It gives internal tools and services a single place to look up product metadata, report on published volume, and manage Adobe InDesign content as it moves through a Crowdin-based localization workflow.

The API is designed for translation teams, localization engineers, production coordinators, and internal web services that need reliable access to LangOps data without working directly against the database or Crowdin by hand.

## What This API Does

This service currently supports three main areas of work:

1. **Product data acces**  
   Search, filter, add, edit, restore, soft-delete, and permanently delete LangOps product records.
3. **Translation reporting**  
   Calculate published word count totals and product-code counts for reporting and planning.
5. **IDML labeling workflow**  
   Extract story-level string groups from Crowdin so they can be labeled and routed during Adobe InDesign localization work.

## Typical Translation Workflow

For IDML-based work, the intended flow is:

1. An IDML file is prepared and uploaded to Crowdin.
2. The API reads the source strings attached to the Crowdin file.
3. Strings are grouped by context identifier, which typically corresponds to an IDML story or content block.
4. A client application or internal tool assigns a label to each group.
5. The API sends those labels back to Crowdin so the content can be organized for downstream translation work.

This makes it easier to separate article content from short miscellaneous strings such as navigation labels, notes, or small fragments that should be handled differently.

## Authentication

This API sits behind Cloudflare Zero Trust and requires a valid `CF_Authorization` JWT on protected routes.

Authentication behavior:

1. The caller sends a `CF_Authorization` header.
2. The API validates the token signature against Cloudflare Access public keys.
3. The token issuer must match the configured Cloudflare team URL.
4. The audience must match one of the trusted internal applications.

This API is intended for internal services and trusted applications. It is not designed as a public internet-facing API.

## Base Path

All application routes are mounted under:

```text
/api/v1
```

## Main Route Groups

### API Status

- `GET /api/v1/status/health`
	Checks database connectivity and returns the current database version.

### Products

- `GET /api/v1/products`
	Returns paginated product results with filters such as target language, publication date range, product code, media group, and deletion state.
- `GET /api/v1/products/{id}`
	Retrieves a single product by UUID.
- `GET /api/v1/products/wordcount`
	Returns the sum of published word counts for matching products.
- `GET /api/v1/products/productcount`
	Returns published product counts grouped by product code.
- `POST /api/v1/products/add`
	Adds one or more products.
- `PATCH /api/v1/products/edit/{id}`
	Updates an existing product.
- `PATCH /api/v1/products/restore/{id}`
	Restores a soft-deleted product.
- `DELETE /api/v1/products/delete/{id}`
	Soft-deletes a product.
- `DELETE /api/v1/products/permanentdelete/{id}`
	Permanently deletes a product.

### IDML Operations

- `GET /api/v1/idml/map/{crowdin_project_id}/{crowdin_file_id}`
	Returns grouped source strings for a Crowdin file so a client can review and label each context group.
- `POST /api/v1/idml/label/{crowdin_project_id}`
	Applies labels in Crowdin using the reviewed schema payload.

## IDML Mapping Shape

The IDML mapping endpoint returns a list of grouped items. Each item represents one context identifier and the strings associated with it.

Example response shape:

```json
{
	"data": [
		{
			"context_identifier": "A1B2C3",
			"map": {
				"string_ids": [101, 102, 103],
				"strings": [
					"Main article headline",
					"Deck copy",
					"Body paragraph"
				],
				"label_id": null
			}
		}
	]
}
```

This structure is meant to be easy for a frontend or internal tool to display to translators, editors, or coordinators who need to decide how each content group should be labeled.

## Label Submission Shape

The label endpoint expects a JSON body containing a list of the same grouped items, with `label_id` populated where applicable.

Example request body:

```json
[
	{
		"context_identifier": "A1B2C3",
		"map": {
			"string_ids": [101, 102, 103],
			"strings": [
				"Main article headline",
				"Deck copy",
				"Body paragraph"
			],
			"label_id": 1412
		}
	}
]
```

In the current workflow:

- smaller string groups can be treated as miscellaneous content
- larger groups can be assigned a Crowdin label for article-level handling

## Environment Variables

Set the following environment variables before running the API locally.

### Database

- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`

Optional:

- `URL`
	Full SQLAlchemy database URL. If omitted, the app builds a PostgreSQL connection string from the `DB_*` values.

### Cloudflare Access

- `CF_TEAM_URL`
- `API_AUD_TAG`
- `LANGOPS_WEBSITE_AUD_TAG`

### Crowdin

- `CROWDIN_API_TOKEN`

## Local Setup

### 1. Create and activate a virtual environment

PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment variables

Example PowerShell session:

```powershell
$env:DB_USER = "your_db_user"
$env:DB_PASSWORD = "your_db_password"
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_NAME = "langops"
$env:CF_TEAM_URL = "https://your-team.cloudflareaccess.com"
$env:API_AUD_TAG = "your_api_audience"
$env:LANGOPS_WEBSITE_AUD_TAG = "your_frontend_audience"
$env:CROWDIN_API_TOKEN = "your_crowdin_token"
```

### 4. Start the API

```powershell
fastapi dev .\main.py
```

### 5. Open the interactive docs

Once the server is running locally, open:

```text
http://127.0.0.1:8000/docs
```

## Error Handling

The API uses structured JSON error responses for common failure cases, including:

- `400 Bad Request`
- `401 Unauthorized`
- `404 Not Found`
- `422 Unprocessable Content`
- `500 Internal Server Error`

This helps client applications distinguish between bad input, authentication failures, missing records, and internal processing problems.

## Repository Layout

```text
auth.py                Cloudflare Access token verification
db.py                  Async database engine and session management
main.py                FastAPI app configuration, middleware, and exception handling
models.py              SQLAlchemy ORM models
routers/               Route groups for status, products, and IDML operations
schemas/               Pydantic request, response, error, and data contracts
functions.py           Crowdin and IDML helper functions
create_tables.sql      Database schema bootstrap SQL
```

## Notes For Translation Teams

This project is built around production localization realities:

- product metadata needs to be searchable by language, product code, and publication state
- volume reporting needs to reflect published work only
- IDML content often needs grouping before assignment and translation
- small non-article strings frequently need separate handling from main article content

If you are building a translation dashboard or intake workflow on top of this API, the IDML mapping and labeling routes are the main integration points to start with.

