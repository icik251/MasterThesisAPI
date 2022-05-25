from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# This is what we expect in the POST request for company
class Scaler(BaseModel):
    k_fold: int = Field(...)
    list_of_features_to_scale: Optional[List] = [
        "fundamental_data_diff_self_t_1",
        "fundamental_data_diff_self_t_2",
        "fundamental_data_diff_industry_t",
        "fundamental_data_diff_industry_t_1",
        "fundamental_data_diff_industry_t_2",
    ]

    class Config:
        schema_extra = {
            "example": {
                "k_fold": 1,
                "list_of_features_to_scale": [
                    "fundamental_data_diff_self_t_1",
                    "fundamental_data_diff_self_t_2",
                    "fundamental_data_diff_industry_t",
                    "fundamental_data_diff_industry_t_1",
                    "fundamental_data_diff_industry_t_2",
                ],
            }
        }
