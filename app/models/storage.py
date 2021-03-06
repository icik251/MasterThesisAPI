from typing import Any
from pydantic import BaseModel, Field

from models.quarter import Quarter
from utils import PyObjectId
from bson import ObjectId

from datetime import datetime

# This is the representation of how the data is going to be stored in MongoDB
class Storage(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    dumped_object: Any = Field(...)
    name: str = Field(...)
    k_fold: Any = Field(...)
    date_created: datetime = datetime.now()

    class Config:
        allow_population_by_field_name = True
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
