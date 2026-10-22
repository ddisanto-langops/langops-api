# LangOps API

LangOps API is a FastAPI service for translation operations at scale. It provides a single source of truth for interacting with all product data and automations, and is meant to make these interactions traceable. The API is intended for a PostgreSQL database.  
Setting up the API is simplified using docker-compose. See the necessary environment variables below.

## Contents
- [What This API Does](#what-this-api-does)
- [Authentication](#authentication)
- [Base Path](#base-path)
- [Main Route Groups](#main-route-groups)
- [Environment Variables](#environment-variables)
- [Error Handling](#error-handling)
- [Example IDML Workflow](#example-idml-workflow)



## What This API Does

This API provides three main service categories:

1. **Product data access**  
   Search, filter, add, edit, soft-delete, restore, and permanently delete LangOps product records.
3. **Translation reporting**  
   Calculate published word count totals and product code counts for reporting and planning.
5. **IDML labeling workflow**  
   Extract story-level string groups from Crowdin so they can be labeled and assigned for translation, avoiding context-loss during localization of Adobe InDesign files.
4. **Webhook monitoring**.  
	The API allows users to `POST` failed webhooks to the database pending inspection and resolution, along with `GET` and `DELETE` operations.

## Authentication

This API makes use of Cloudflare's Zero Trust architecture and requires a valid `Cf-Access-Jwt-Assertion` JWT on all routes (via Service Auth Token).

Authentication behavior:

1. Caller must send a `Cf-Access-Jwt-Assertion` header; the API validates the token signature against Cloudflare Access public keys. 
2. The token issuer must match the configured Cloudflare team URL.
3. The audience must match one of the trusted internal applications.

## Base Path

All application routes are mounted under:

```text
/api/v1
```

## Main Route Groups

### API Status

- `HEAD /api/v1/status`  
	Basic connectivity check
- `GET /api/v1/status/database`  
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
- `GET /api/v1/webhooks/failures`  
	Fetch all webhook data posted to the API (intended for monitoring failed requests)
- `POST /api/v1/webhooks/failures`  
	Send a failed webhook to be stored in the DB  
- `DELETE /api/v1/webhooks/failures/delete/{id}`  
	Delete a webhook record

## Environment Variables

Set the following environment variables before running the API:

### Environment
- `ENVIRONMENT`  
	One of `DEV` or `PROD`. If using dev mode, the Cf-Access-Jwt-Assertion is not checked, to permit local testing (use `CF-Client-Access-ID` and `CF-Client-Access-Secret` instead). Ensure this is set to `PROD` before deployment!

### Database

- `DB_USER`: name of the user which has access to the database
- `DB_PASSWORD`: password for the database
- `DB_HOST`: if using Docker, make sure to set this to the appropriate service name
- `DB_PORT`: PostgreSQL default is 5432
- `DB_NAME`

### Cloudflare Access
- `CF_TEAM_URL`: used to validate JWT
- `TRUSTED_AUDIENCES` (for multiple audiences, use the format "audience1, audience2, audience3")

### Crowdin
- `CROWDIN_API_TOKEN`: used for the IDML automations

## Error Handling

The API supports common error responses such as:
- `400 Bad Request`
- `401 Unauthorized`
- `404 Not Found`
- `405 Method Not Allowed`
- `422 Unprocessable Content`
- `500 Internal Server Error`


## Example IDML Workflow
This section provides a look at how the labeling of inDesign files takes place.  
The workflow is as follows:

1. An IDML file is prepared and uploaded to Crowdin.
2. Upon request, the API reads the source strings attached to the Crowdin file.
3. Strings are grouped by context identifier, which corresponds to an IDML story or content block (see [IDML Mapping Shape](#idml-mapping-shape) below).
4. A client application or internal tool assigns a label to each group.
5. The API sends those labels back to Crowdin so the content can be organized for translation work.

This has the added benefit of separating articles from the TOC and miscellaneous strings such as callout boxes.

### IDML Mapping Shape

The IDML mapping endpoint returns a list of grouped items. Each item represents one context identifier and the strings associated with it.  
This JSON is meant for a front-end where end-users such as language managers will add labels to each group of strings.
Example response shape:

```json
{
	"data": [
		{
			"context_identifier": "A1B2C3",
			"map": {
				"string_ids": [1, 2, 3],
				"strings": [
					"First sentence",
					"Second sentence",
					"and so on"
				],
				"label_id": null // will be set by cient; see below
			}
		}
	]
}
```



### Label Submission Shape

The label endpoint expects a JSON body containing a list of the same grouped items, with `label_id` populated where applicable.  
Note that the label text itself must be created in Crowdin (this can be done programmatically via the client application).  
The API simply needs to know the ID of the label.

Example request body:

```json
[
	{
		"context_identifier": "A1B2C3",
		"map": {
			"string_ids": [1, 2, 3],
			"strings": [
				"First sentence",
				"Second sentence",
				"and so on"
			],
			"label_id": 1412 // client app has generated a label, retrieved its ID and passed it to the API
		}
	}
]
```

NOTE: in the current workflow:
- groups of less than 10 strings are treated as miscellaneous content (TOC, ads, etc.)
- groups of 10 or greater can be assigned a Crowdin label for article-level handling