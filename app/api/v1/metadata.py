import json
from typing import Any, Optional
from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from databases.mongodb.session import get_database_async
from crud.company import get_company_async

from schemas.metadata import Metadata, ErrorResponseModel
from celery_worker import create_metadata

from utils import parse_model_to_dict
from bson import json_util

router = APIRouter()


@router.post("/", response_description="Metadata data added into the queue")
async def add_metadata(
    metadata: Metadata = Body(...), db: AsyncIOMotorClient = Depends(get_database_async)
):
    metadata_dict = metadata.dict()
    curr_company = await get_company_async(
        db, metadata_dict["cik"], metadata_dict["year"]
    )

    if curr_company:
        create_metadata.delay(metadata_dict, parse_model_to_dict(curr_company))
        return {"message": "Task added to queue."}
    else:
        return ErrorResponseModel(
            "An error occurred.",
            404,
            "Company doesn't exist, therefore metadata can't be added.",
        )
