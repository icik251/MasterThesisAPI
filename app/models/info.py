from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from utils import PyObjectId
from bson import ObjectId

# This is the representation of how the data is going to be stored in MongoDB
class Info(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    type: str = Field(...)  # the field thing means it is required
    filing_date: datetime = Field(...)
    period_of_report: datetime = Field(...)
    url_htm: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "type": "10-Q",
                "filing_date": datetime(2020, 2, 14),
                "period_of_report": datetime(2020, 10, 2),
                "url_htm": "https://www.sec.gov/Archives/edgar/data/1318605/000156459020004475/tsla-10k_20191231.htm",
            }
        }


class UpdateInfo(BaseModel):
    type: Optional[str]
    filing_date: Optional[datetime]
    period_of_report: Optional[datetime]
    uri_htm: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "type": "10-Q",
                "filing_date": datetime(2020, 2, 14),
                "period_of_report": datetime(2020, 10, 2),
                "url_htm": "https://www.sec.gov/Archives/edgar/data/1318605/000156459020004475/tsla-10k_20191231.htm",
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
