from typing import Optional
from pydantic import BaseModel, Field

from utils import PyObjectId
from bson import ObjectId

# This is the representation of how the data is going to be stored in MongoDB
class AdapterData(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    text: str = Field(...)
    data_type: str = Field(...)
    label: str = Field(...)
    k_fold_config: dict = {}

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UpdateAdapterData(BaseModel):
    text: Optional[str]  # the field thing means it is required
    data_type: Optional[str]
    label: Optional[str]
    k_fold_config: Optional[dict]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
