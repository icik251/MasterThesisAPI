from typing import Optional
from pydantic import BaseModel, Field

# class PyObjectId(ObjectId):
#     @classmethod
#     def __get_validators__(cls):
#         yield cls.validate

#     @classmethod
#     def validate(cls, v):
#         if not ObjectId.is_valid(v):
#             raise ValueError("Invalid objectid")
#         return ObjectId(v)

#     @classmethod
#     def __modify_schema__(cls, field_schema):
#         field_schema.update(type="string")

# This is the representation of how the data is going to be stored in MongoDB
class Company(BaseModel):
    cik: int = Field(...) # the field thing means it is required
    name: str = Field(...) 
    year: int = Field(..., gt=1990)

    class Config:
        schema_extra = {
            "example": {
                "cik": 1000045,
                "name": "Nicholas Financial Inc",
                "year": 2020
            }
        }

class UpdateCompany(BaseModel):
    cik: Optional[int] # the field thing means it is required
    name: Optional[str]
    year: Optional[int]

    class Config:
        schema_extra = {
            "example": {
                "cik": 1000045,
                "name": "Nicholas Financial Inc",
                "year": 2020
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
