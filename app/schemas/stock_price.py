from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# This is what we expect in the POST request for metadata
class StockPrice(BaseModel):
    cik: int = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "cik": 1000045,
            }
        }


# def ResponseModel(data, message):
#     # if only 1 company, put it in a list for general response with multiple companies
#     if not isinstance(data, list):
#         data = [data]
#     return {
#         "data": data,
#         "code": 200,
#         "message": message,
#     }


def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
