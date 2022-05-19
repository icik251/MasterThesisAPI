from typing import Optional
from pydantic import BaseModel, Field

# This is what we expect in the POST request for company
class AdapterData(BaseModel):
    text: str = Field(...)
    data_type: str = Field(...)
    label: str = Field(...)
    k_fold_config: dict = {}


class UpdateAdapterData(BaseModel):
    text: Optional[str]  # the field thing means it is required
    data_type: Optional[str]
    label: Optional[str]
    k_fold_config: Optional[dict]


def ResponseModel(data, message):
    # if only 1 company, put it in a list for general response with multiple companies
    if not isinstance(data, list):
        data = [data]
    return {
        "data": data,
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
