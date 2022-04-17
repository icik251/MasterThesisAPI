from pydantic import BaseModel, Field

# This is what we expect in the POST request for company
class FundamentalData(BaseModel):
    cik: int = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "cik": 1000045,
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
