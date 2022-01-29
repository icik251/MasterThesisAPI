from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from ..models.quarter import Quarter
from ..utils import PyObjectId
from bson import ObjectId

# This is the representation of how the data is going to be stored in MongoDB
class Company(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cik: int = Field(...) # the field thing means it is required
    name: str = Field(...) 
    year: int = Field(..., gt=1990)
    quarters: List[Quarter]
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "cik": 1000045,
                "name": "Nicholas Financial Inc",
                "year": 2020,
                "quarters": [
                                {'q':1, 'metadata': 
                                    [
                                        {"type": "10-Q",
                                         "date": datetime(2020,2,14),
                                         "uri_txt": "smt/smt/smt.txt",
                                         "uri_html": "smt/smt/smt.html"
                                        },
                                    ]
                                },
                            ]
                        }
                    }

class UpdateCompany(BaseModel):
    cik: Optional[int] # the field thing means it is required
    name: Optional[str]
    year: Optional[int]
    quarters: Optional[List[Quarter]]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "cik": 1000045,
                "name": "Nicholas Financial Inc",
                "year": 2020,
                "quarters": [
                                {'q':1, 'metadata': 
                                    [
                                        {"type": "10-Q",
                                         "date": datetime(2020,2,14),
                                         "uri_txt": "smt/smt/smt.txt",
                                         "uri_html": "smt/smt/smt.html"
                                        },
                                    ]
                                },
                            ]
                        }
                    }


def ResponseModel(data, message):
    return {
        "data": Company(**data),
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
