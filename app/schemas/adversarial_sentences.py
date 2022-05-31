from typing import Dict
from pydantic import BaseModel, Field

# This is what we expect in the POST request for company
class AdversarialSentences(BaseModel):
    dict_of_sentiment_sentence: dict = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "dict_of_sentiment_sentence": {
                    "positive": "The company is doing awesome",
                    "negative": "Everything is going extremely bad",
                }
            }
        }
