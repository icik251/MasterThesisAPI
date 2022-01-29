from fastapi import APIRouter, Body

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
    new_company = await add_company(company.dict(by_alias=True))
    # return ResponseModel(new_company, "Company added successfully.")
    return ResponseModel(new_company, "Company added successfully.")