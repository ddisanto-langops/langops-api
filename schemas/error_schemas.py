from pydantic import BaseModel
from datetime import datetime


# ----------------------------------------------
# The models of each individual error response
# ----------------------------------------------
class ErrorDetail(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class BadRequestError(BaseModel):
    # 400
    error_code: str = "BAD_REQUEST"
    message: str = "Bad data sent to server"
    timestamp: datetime


class Unauthorized(BaseModel):
    # 401
    error_code: str = "Unauthorized"
    message: str = "Token is missing, expired or incorrect"
    timestamp: datetime


class NotFoundError(BaseModel):
    # 404
    error_code: str = "NOT_FOUND"
    message: str = "Record was not found"
    timestamp: datetime


class MethodNotAllowedError(BaseModel):
    # 405
    error_code: str = "METHOD_NOT_ALLOWED"
    message: str = "This endpoint does not accept the provided method"
    timestamp: datetime


class ClientValidationError(BaseModel):
    # 422
    error_code: str = "INVALID_INPUT_PAYLOAD"
    message: str = "The request payload failed validation rules."
    details: list[ErrorDetail]
    timestamp: datetime

class ServerContractViolation(BaseModel):
    # 500
    error_code: str = "SERVER_CONTRACT_VIOLATION"
    message: str = "Internal server configuration error."
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
        "description": "Data sent to the server was malformed."
    }

    _401_UNAUTHORIZED = {
        "model": Unauthorized,
        "description": "Token missing, expired or incorrect"
    }

    _404_NOT_FOUND = {
        "model": NotFoundError,
        "description": "The requested LangOps resource could not be located."
    }

    _405_METHOD_NOT_ALLOWED = {
        "model": MethodNotAllowedError,
        "description": "The client tried to use a method which this endpoint does not allow."
    }
    
    _422_VALIDATION_ERROR = {
        "model": ClientValidationError,
        "description": "The client sent a payload that failed schema or domain validation."
    }
    
    _500_INTERNAL_SERVER_ERROR = {
        "model": ServerContractViolation,
        "description": "Internal database structure or outbound schema mismatch."
    }

    
