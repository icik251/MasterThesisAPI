from datetime import datetime
from operator import mod
from typing import List, Optional
from pydantic import BaseModel, Field

from models import company as model_company

# This is what we expect in the POST request for company
class Company(BaseModel):
    cik: int = Field(...)
    name: str = Field(...)
    year: int = Field(...)
    quarter: int = Field(...)
    type: str = Field(...)
    filing_date: datetime = Field(...)
    html_path: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "cik": 1000045,
                "name": "Nicholas Financial Inc",
                "year": 2020,
                "quarter": 1,
                "type": "10-Q",
                "filing_date": datetime(20, 5, 2),
                "html_path": "edgar/data/1000045/0001193125-12-047920-index.html",
            }
        }


class UpdateCompany(BaseModel):
    cik: Optional[int]  # the field thing means it is required
    name: Optional[str]
    year: Optional[int]
    quarter: Optional[int]
    type: Optional[str]
    filing_date: Optional[datetime]
    html_path: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "cik": 1000045,
                "name": "Nicholas Financial Inc",
                "year": 2020,
                "quarter": 1,
                "type": "10-Q",
                "filing_date": datetime(20, 5, 2),
                "html_path": "edgar/data/1000045/0001193125-12-047920-index.html",
            }
        }


def ResponseModel(data, message):
    return {
        "data": model_company.Company(**data),
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
