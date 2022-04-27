from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from utils import PyObjectId
from bson import ObjectId

# This is the representation of how the data is going to be stored in MongoDB
class InputData(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cik: int = Field(...)  # the field thing means it is required
    sector: Optional[str] = None
    industry: Optional[str] = None
    year: int = Field(...)
    type: str = Field(...)
    q: int = Field(...)
    mda_section: Optional[str] = None
    risk_section: Optional[str] = None
    company_type: str = Field(...)
    filing_date: datetime = Field(...)
    deadline_date: Optional[datetime] = None
    period_of_report: datetime = Field(...)
    is_filing_on_time: bool = Field(...)
    close_price_date: datetime = Field(...)
    close_price: float = Field(...)
    volume: float = Field(...)
    close_price_next_date: datetime = Field(...)
    close_price_next_day: float = Field(...)
    volume_next_day: float = Field(...)
    label: Optional[str] = None
    percentage_change: Optional[float] = None
    percentage_change_scaled_min_max: Optional[dict] = {}
    percentage_change_scaled_standard: Optional[dict] = {}
    k_fold_config: dict = Field(...)
    mda_paragraphs: Optional[dict] = {}
    risk_paragraphs: Optional[dict] = {}
    fundamental_data: Optional[dict] = {}
    fundamental_data_imputed: Optional[dict] = {}
    fundamental_data_avg: Optional[dict] = {}
    fundamental_data_diff: Optional[dict] = {}

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
