from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from ..models.metadata import Metadata
from ..utils import PyObjectId
from bson import ObjectId

# This is the representation of how the data is going to be stored in MongoDB
class Quarter(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    q: int = Field(..., gt=0, le=4) # the field thing means it is required
    metadata: List[Metadata]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "q": 1,
                "metadata": [
                                {"type": "10-Q",
                                    "date": datetime(2020,2,14),
                                    "uri_txt": "smt/smt/smt.txt",
                                    "uri_html": "smt/smt/smt.html"
                                },
                            ]
            }
        }

class UpdateQuarter(BaseModel):
    q: Optional[int] # the field thing means it is required
    metadata: Optional[List[Metadata]]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "q": 1,
                "metadata": [
                                {"type": "10-Q",
                                    "date": datetime(2020,2,14),
                                    "uri_txt": "smt/smt/smt.txt",
                                    "uri_html": "smt/smt/smt.html"
                                },
                            ]
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
