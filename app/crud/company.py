from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from core import settings
from models import company as model_company


# async def add_company_async(
#     db: AsyncIOMotorClient,
#     company_data: dict,
#     company_collection: str = settings.COMPANY_COLLECTION,
# ) -> dict:
#     company = await db[company_collection].insert_one(company_data)
#     new_company = await db[company_collection].find_one({"_id": company.inserted_id})
#     return new_company


async def get_company_async(
    db: AsyncIOMotorClient,
    cik: int,
    year: int,
    company_collection: str = settings.COMPANY_COLLECTION,
) -> Any:
    if year:
        company = await db[company_collection].find_one({"cik": cik, "year": year})
        if company:
            return model_company.Company(**company)
    else:
        company_list = []
        async for company in db[company_collection].find({"cik": cik}):
            company_list.append(model_company.Company(**company))
        return company_list


def add_company(
    db: MongoClient,
    company_data: dict,
    company_collection: str = settings.COMPANY_COLLECTION,
) -> dict:
    company = db[company_collection].insert_one(company_data)
    new_company = db[company_collection].find_one({"_id": company.inserted_id})
    return new_company


def get_company(
    db: MongoClient,
    company_data: dict,
    company_collection: str = settings.COMPANY_COLLECTION,
) -> dict:
    return db[company_collection].find_one(
        {
            "cik": company_data["cik"],
            "name": company_data["name"],
            "year": company_data["year"],
        }
    )
