from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# This is what we expect in the POST request for metadata
class StockPrice(BaseModel):
    cik: int = Field(...)
    start_date: Optional[str] = "1993-01-01"
    end_date: Optional[str] = "2022-02-01"

    class Config:
        schema_extra = {
            "example": {
                "cik": 1000045,
                "start_date": "2017-01-01",
                "end_date": "2017-04-30",
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
