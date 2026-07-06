# LangOps API

LangOps API is a FastAPI service for translation operations at scale. It gives internal services a single source of truth for interacting with product data and managing localization of Adobe InDesign content. It is meant to provide a clear and auditable contract between any localization service and stored LangOps data. This API sits above a PostgreSQL database and is designed to interact with other server-side tools. It is not internet-facing.

## Contents
- [What This API Does](#what-this-api-does)
- [Authentication](#authentication)
- [Base Path](#base-path)
- [Main Route Groups](#main-route-groups)
- [Environment Variables](#environment-variables)
- [Error Handling](#error-handling)
- [Example IDML Workflow](#example-idml-workflow)



## What This API Does

This API provides three main services:

1. **Product data acces**  
   Search, filter, add, edit, soft-delete, restore, and permanently delete LangOps product records.
3. **Translation reporting**  
   Calculate published word count totals and product code counts for reporting and planning.
5. **IDML labeling workflow**  
   Extract story-level string groups from Crowdin so they can be labeled and assigned for translation, avoiding context-loss  during Adobe InDesign localization work.

## Authentication

This API makes use of Cloudflare Zero Trust architecture and requires a valid `CF_Authorization` JWT on all routes.

Authentication behavior:

1. Caller must send a `CF_Authorization` header; the API validates the token signature against Cloudflare Access public keys. 
2. The token issuer must match the configured Cloudflare team URL.
3. The audience must match one of the trusted internal applications.

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

### Webhooks
- `HEAD /api/v1/webhooks/trello`
	Route to allow Trello to check connectivity at time of webhook creation
- `POST /api/v1/webhooks/trello`
	Endpoint for all Trello webhooks. Action, action date and card ID are extracted, and returned to inform the caller of which Trello card was updated.

## Environment Variables

Set the following environment variables before running the API:

### Database

- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`


### Cloudflare Access

- `CF_TEAM_URL`
- `TRUSTED_AUDIENCES` (in the format)

### Crowdin

- `CROWDIN_API_TOKEN`

## Error Handling

The API uses structured JSON error responses for common failure cases, including:

- `400 Bad Request`
- `401 Unauthorized`
- `404 Not Found`
- `422 Unprocessable Content`
- `500 Internal Server Error`

This helps client applications distinguish between bad input, authentication failures, missing records, and internal processing problems.


## Example IDML Workflow

For IDML-based work, the intended flow is:

1. An IDML file is prepared and uploaded to Crowdin.
2. Upon request, the API reads the source strings attached to the Crowdin file.
3. Strings are grouped by context identifier, which corresponds to an IDML story or content block (see [IDML Mapping Shape](#idml-mapping-shape) below).
4. A client application or internal tool assigns a label to each group.
5. The API sends those labels back to Crowdin so the content can be organized for translation work.

This has the added effect of separating articles from the TOC, headers, and so forth.

### IDML Mapping Shape

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

This structure is meant to be easy for a frontend or internal tool to display to language managers who need to decide how each content group should be labeled.

### Label Submission Shape

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

- groups of less than 10 strings are treated as miscellaneous content (TOC, ads, etc.)
- groups of 10 or greater can be assigned a Crowdin label for article-level handling