from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# This is what we expect in the POST request for company
class KFolds(BaseModel):
    k_folds_rules: dict = Field(...)
