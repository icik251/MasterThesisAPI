from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# This is what we expect in the POST request for company
class Scaler(BaseModel):
    k_fold: int = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "k_fold": 1
            }
        }