from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder

from ..database import (
    add_company,
)

from ..models.company import (
    ErrorResponseModel,
    ResponseModel,
    Company,
    UpdateCompany,
)

router = APIRouter()

@router.post("/", response_description="Company data added into the database")
async def add_company_data(company: Company = Body(...)):
    company = jsonable_encoder(company)
    new_company = await add_company(company)
    return ResponseModel(new_company, "Company added successfully.")