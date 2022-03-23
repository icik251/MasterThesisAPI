import json
from typing import Any, Optional
from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from crud.company import fix_company, update_company, get_all_companies_async
from crud.company import get_company_async, get_duplicated_companies

# from crud.company import add_company
from schemas.company import Company, ResponseModel, ErrorResponseModel
from celery_worker import create_company
from databases.mongodb.session import get_database_async

from models.company import UpdateCompany

router = APIRouter()


@router.post("/", response_description="Company data added into the queue")
def add_company_data(company: Company = Body(...)):
    create_company.delay(company.dict())
    return {"message": "Task added to queue."}


@router.get("/{cik}", response_description="Get data for company")
async def get_company_data(
    cik: int,
    year: Optional[int] = None,
    db: AsyncIOMotorClient = Depends(get_database_async),
):
    company_res = await get_company_async(db, cik, year)
    if company_res:
        return ResponseModel(company_res, "Company retrieved")
    else:
        return ErrorResponseModel("An error occurred.", 404, "Company doesn't exist.")


@router.get("/", response_description="Get all companies in the DB")
async def get_all_companies_data(db: AsyncIOMotorClient = Depends(get_database_async)):
    company_res = await get_all_companies_async(db)
    if company_res:
        return ResponseModel(company_res, "All companies retrieved")
    else:
        return ErrorResponseModel("An error occurred.", 404, "Companies doesn't exist.")


@router.get(
    "/duplicated/",
    response_description="Get all companies that have duplicated data (race condition when adding them)",
)
async def get_duplicated_company_data(
    db: AsyncIOMotorClient = Depends(get_database_async),
):
    return await get_duplicated_companies(db)


@router.put(
    "/duplicated/{cik}/{year}", response_description="Fix duplicate company and get it"
)
async def fix_duplicate_company_data(
    cik: int, year: int, db: AsyncIOMotorClient = Depends(get_database_async)
):

    inserted_company = await fix_company(db, cik, year)
    return ResponseModel(inserted_company, "Company duplication fixed and retrieved")


@router.put(
    "/filing_type/{cik}/{year}",
    response_description="Fix filing type for company for year",
)
async def fix_filing_type(
    cik: int,
    year: int,
    updated_company: UpdateCompany = Body(...),
    db: AsyncIOMotorClient = Depends(get_database_async),
):
    inserted_company = await update_company(cik, year, updated_company.dict(), db)
    return ResponseModel(
        inserted_company, "Company filing types updated and company retrieved"
    )
