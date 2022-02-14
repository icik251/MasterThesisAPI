from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from utils import PyObjectId
from bson import ObjectId

# This is the representation of how the data is going to be stored in MongoDB
class Metadata(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cik: int = Field(...)
    year: int = Field(...)
    quarter: int = Field(...)
    type: str = Field(...)  # the field thing means it is required
    mda_section: Optional[str] = None
    risk_section: Optional[str] = None
    assets: Optional[List] = []
    liabilities: Optional[List] = []
    liabilities_and_stockholders_equity: Optional[List] = []
    profit_loss: Optional[Dict] = {}
    # revenues: Optional[Dict] = {}

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
