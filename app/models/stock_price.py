from datetime import date, datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from utils import PyObjectId
from bson import ObjectId

# This is the representation of how the data is going to be stored in MongoDB
class StockPrice(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    metadata: Dict = Field(...)
    timestamp: datetime = Field(...)
    open: float = Field(...)
    high: float = Field(...)
    low: float = Field(...)
    close: float = Field(...)
    adjusted_close: float = Field(...)
    volume: float = Field(...)
    divident_amount: float = Field(...)
    split_coeff: float = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
