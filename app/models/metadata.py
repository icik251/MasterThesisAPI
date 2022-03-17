from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from utils import PyObjectId
from bson import ObjectId

# This is the representation of how the data is going to be stored in MongoDB
class Metadata(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    type: str = Field(...)  # the field thing means it is required
    filing_date: datetime = Field(...)
    period_of_report: datetime = Field(...)
    filing_url: str
    risk_section: str = None
    mda_section: str = None
    qqd_section: str = None
    company_type: str = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "type": "10-Q",
                "filing_date": datetime(2020, 2, 14),
                "period_of_report": datetime(2020, 10, 2),
                "filing_url": "https://www.sec.gov/Archives/edgar/data/66740/0000066740-94-000021.txt",
                "risk_section": "text for risk",
                "mda_section": "text for mda",
                "qqd_section": "text for qqd",
                "company_type": "accelerated_filer",
            }
        }


# def ResponseModel(data, message):
#     return {
#         "data": data,
#         "code": 200,
#         "message": message,
#     }


# def ErrorResponseModel(error, code, message):
#     return {"error": error, "code": code, "message": message}
