from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# This is what we expect in the POST request for company
class Company(BaseModel):
    cik: int = Field(...)
    name: str = Field(...)
    ticker: str = None
    sector: str = None
    industry: str = None
    year: int = Field(...)
    quarter: int = Field(...)
    type: Optional[str]
    filing_date: Optional[datetime]
    index_url: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "cik": 1000045,
                "name": "Nicholas Financial Inc",
                "ticker": "NICK",
                "year": 2020,
                "quarter": 1,
                "type": "10-Q",
                "filing_date": datetime(20, 5, 2),
                "index_url": "https://www.sec.gov/Archives/edgar/data/1000045/0001193125-12-047920-index.html",
            }
        }


class UpdateCompany(BaseModel):
    cik: Optional[int]  # the field thing means it is required
    name: Optional[str]
    ticker: Optional[str]
    year: Optional[int]
    quarter: Optional[int]
    type: Optional[str]
    filing_date: Optional[datetime]
    index_url: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "cik": 1000045,
                "name": "Nicholas Financial Inc",
                "ticker": "NICK",
                "year": 2020,
                "quarter": 1,
                "type": "10-Q",
                "filing_date": datetime(20, 5, 2),
                "index_url": "https://www.sec.gov/Archives/edgar/data/1000045/0001193125-12-047920-index.html",
            }
        }


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
