from schemas.base import CamelModel
from datetime import datetime
from fastapi import status


# ----------------------------------------------
# The models of each individual error response
# ----------------------------------------------
class ErrorDetail(CamelModel):
    loc: list[str | int]
    msg: str
    type: str


class BadRequestError(CamelModel):
    error_code: int = status.HTTP_400_BAD_REQUEST
    message: str = "Bad data sent to server"
    timestamp: datetime


class Unauthorized(CamelModel):
    error_code: int = status.HTTP_401_UNAUTHORIZED
    message: str = "Token is missing, expired or incorrect"
    timestamp: datetime


class NotFoundError(CamelModel):
    error_code: int = status.HTTP_404_NOT_FOUND
    message: str = "Record was not found"
    timestamp: datetime


class MethodNotAllowedError(CamelModel):
    error_code: int = status.HTTP_405_METHOD_NOT_ALLOWED
    message: str = "This endpoint does not accept the provided method"
    timestamp: datetime


class ClientValidationError(CamelModel):
    error_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT
    message: str = "The request payload failed validation rules."
    details: list[ErrorDetail]
    timestamp: datetime

class ServerContractViolation(CamelModel):
    error_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Internal server configuration error."
    timestamp: datetime

class BadGateway(CamelModel):
    error_code: int = status.HTTP_502_BAD_GATEWAY
    message: str = "Upstream error"
    timestamp: datetime


# ------------------------------------------------------------------------------
# A class from which all the available models can be selected in routes;
# maps the error model to a standard HTTP error code for easy selection.
# ------------------------------------------------------------------------------
class ErrorResponses:
    """
    A static catalog of standardized OpenAPI responses for documentation.
    Follows the FastAPI format of model, description. Must be preceded in 
    routes with the actual status code (int) which can be provided by the
    status code library.
    """
    
    _400_BAD_REQUEST = {
        "model": BadRequestError,
        "description": "Data sent to the server was malformed"
    }

    _401_UNAUTHORIZED = {
        "model": Unauthorized,
        "description": "Token missing, expired or incorrect"
    }

    _404_NOT_FOUND = {
        "model": NotFoundError,
        "description": "The requested LangOps resource could not be located"
    }

    _405_METHOD_NOT_ALLOWED = {
        "model": MethodNotAllowedError,
        "description": "The client tried to use a method which this endpoint does not allow"
    }
    
    _422_VALIDATION_ERROR = {
        "model": ClientValidationError,
        "description": "The client sent a payload that failed schema or domain validation"
    }
    
    _500_INTERNAL_SERVER_ERROR = {
        "model": ServerContractViolation,
        "description": "Internal database structure or outbound schema mismatch"
    }

    _502_BAD_GATEWAY = {
        "model": BadGateway,
        "description": "Error from upstream resource"
    }

    
