from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, # Emit camel case
        populate_by_name=True  # allow snake_case internally
    )

class CamelJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return super().render(jsonable_encoder(content, by_alias=True))