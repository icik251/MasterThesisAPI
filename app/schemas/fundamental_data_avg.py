from pydantic import BaseModel, Field

# This is what we expect in the POST request for company
class FundamentalDataAvg(BaseModel):
    year: int = Field(...)
    q: int = Field(...)
    
    class Config:
        schema_extra = {
            "example": {
                "year": 2017,
                "q": 1
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
