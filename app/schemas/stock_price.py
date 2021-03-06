from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# This is what we expect in the POST request for metadata
class StockPrice(BaseModel):
    cik: int = Field(...)
    start_date: Optional[str] = "2017-01-01"

    class Config:
        schema_extra = {
            "example": {
                "cik": 1000045,
                "start_date": "2017-01-01",
            }
        }


def ResponseModel(data, message):
    return {
        "data": data,
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
