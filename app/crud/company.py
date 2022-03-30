import json
from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from schemas.company import Company
from core import settings
from models import company as model_company
from utils import parse_model_to_dict


async def get_company_async(
    db: AsyncIOMotorClient,
    cik: int,
    year: int = None,
    company_collection: str = settings.COMPANY_COLLECTION,
) -> Any:
    if year:
        company = await db[company_collection].find_one({"cik": cik, "year": year})
        if company:
            return model_company.Company(**company)
    else:
        company_list = []
        async for company in db[company_collection].find({"cik": cik}).sort("year", 1):
            company_list.append(model_company.Company(**company))
        return company_list


async def get_all_companies_async(
    db: AsyncIOMotorClient, company_collection: str = settings.COMPANY_COLLECTION
):
    company_list = []
    async for company in db[company_collection].find({}):
        company_list.append(model_company.Company(**company))
    return company_list


async def update_company(
    cik,
    year,
    updated_company,
    db: AsyncIOMotorClient,
    company_collection: str = settings.COMPANY_COLLECTION,
):
    # Delete old
    _ = await db[company_collection].delete_many({"cik": cik, "year": year})
    # Add new
    new_company = await db[company_collection].insert_one(updated_company)
    inserted_company = await db[company_collection].find_one(
        {"_id": new_company.inserted_id}
    )
    return model_company.Company(**inserted_company)


async def get_duplicated_companies(
    db: AsyncIOMotorClient, company_collection: str = settings.COMPANY_COLLECTION
) -> list:
    pipeline = [
        {
            "$group": {
                "_id": {"cik": "$cik", "year": "$year"},
                "uniqueIds": {"$addToSet": "$_id"},
                "count": {"$sum": 1},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]

    list_of_res = []
    async for company in db[company_collection].aggregate(pipeline):
        company = list_of_res.append(company["_id"])

    return list_of_res


async def fix_company(
    db: AsyncIOMotorClient,
    cik: int,
    year: int,
    company_collection: str = settings.COMPANY_COLLECTION,
) -> Company:
    # get from DB
    company_list = []
    async for company in db[company_collection].find({"cik": cik, "year": year}):
        company_list.append(company)

    resulted_company = company_list.pop(0)
    for company in company_list:
        for quarter in company["quarters"]:
            q_processed = False
            for idx, res_quarter in enumerate(resulted_company["quarters"]):
                if quarter["q"] == res_quarter["q"]:
                    # Add new object in metadata
                    for metadata in quarter["metadata"]:
                        resulted_company["quarters"][idx]["metadata"].append(metadata)
                    q_processed = True

            if not q_processed:
                resulted_company["quarters"].append(quarter)

    # resulted_company['quarters'] = sorted(resulted_company['quarters'])
    resulted_company["quarters"] = sorted(
        resulted_company["quarters"], key=lambda x: x["q"]
    )

    # Delete old
    _ = await db[company_collection].delete_many({"cik": cik, "year": year})
    # Add new
    new_company = await db[company_collection].insert_one(resulted_company)
    inserted_company = await db[company_collection].find_one(
        {"_id": new_company.inserted_id}
    )
    return model_company.Company(**inserted_company)


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
