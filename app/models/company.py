from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from models.quarter import Quarter
from utils import PyObjectId
from bson import ObjectId

# This is the representation of how the data is going to be stored in MongoDB
class Company(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cik: int = Field(...)  # the field thing means it is required
    name: str = Field(...)
    sector: Optional[str] = None
    industry: Optional[str] = None
    ticker: Optional[str] = None
    year: int = Field(..., gt=1990)
    quarters: List[Quarter]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UpdateCompany(BaseModel):
    cik: Optional[int]  # the field thing means it is required
    name: Optional[str]
    ticker: Optional[str]
    year: Optional[int]
    quarters: Optional[List[Quarter]]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# def ResponseModel(data, message):
#     return {
#         "data": Company(**data),
#         "code": 200,
#         "message": message,
#     }


# def ErrorResponseModel(error, code, message):
#     return {"error": error, "code": code, "message": message}
