from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from ..utils import PyObjectId
from bson import ObjectId

# This is the representation of how the data is going to be stored in MongoDB
class Metadata(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    type: str = Field(...) # the field thing means it is required
    date: datetime = Field(...) 
    uri_txt: str
    uri_html: str
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "type": "10-Q",
                "date": datetime(2020,2,14),
                "uri_txt": "edgar/data/1000045/0001564590-20-004703.txt",
                "uri_html": "edgar/data/1000045/0001564590-20-004703-index.html"
            }
        }

class UpdateMetadata(BaseModel):
    type: Optional[str]
    date: Optional[datetime] 
    uri_txt: Optional[str]
    uri_html: Optional[str]
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "type": "10-Q",
                "date": datetime(2020,2,14),
                "uri_txt": "edgar/data/1000045/0001564590-20-004703.txt",
                "uri_html": "edgar/data/1000045/0001564590-20-004703-index.html"
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
