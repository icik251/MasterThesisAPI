from services.sec_scraper import SECScraper
from crud.company import add_company, get_company

from databases.mongodb.session import get_database
from databases.mongodb.mongo_utils import connect_to_mongo, close_mongo_connection

from models.company import Company
from models.info import Info
from models.quarter import Quarter

import celery
from celery.signals import celeryd_init
from celery.utils.log import get_task_logger

from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv("../.env")
celery_app = celery.Celery(
    "tasks",
    backend="mongodb://root:root@localhost:27017/",
    broker="amqp://rabbitroot:rabbitroot@localhost:5672//",
)
celery_app.conf.update(
    imports=("celery_worker"),
    mongodb_backend_settings={
        "database": "celery",
        "taskmeta_collection": "celery_taskmeta",
    },
)

celery_log = get_task_logger(__name__)


@celery_app.task(name="create_company")
def create_company(company_dict: dict):
    connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))

    db = get_database(db_name=os.getenv("MONGODB_NAME"))
    company_collection = os.getenv("COMPANY_COLLECTION")

    company_in_db = get_company(
        db=db,
        company_data=company_dict,
        company_collection=company_collection,
    )

    sec_scraper_obj = SECScraper(
        company_dict, geckodriver_path=os.getenv("GECKODRIVER_PATH")
    )
    sec_scraper_obj.logic()

    dict_date_info = sec_scraper_obj.get_date_info()
    period_of_report = None
    if "Period of Report" in dict_date_info:
        period_of_report = datetime.fromisoformat(dict_date_info["Period of Report"])
    htm_uri = sec_scraper_obj.get_htm_url()

    curr_info = Info(
        type=company_dict["type"],
        filing_date=company_dict["filing_date"],
        period_of_report=period_of_report,
        url_htm=htm_uri,
    )

    curr_quarter = Quarter(q=company_dict["quarter"], info=[curr_info.dict()])

    if not company_in_db:
        # initial creation - if company exists only append new quarter, else create new entry
        company_obj = Company(
            cik=company_dict["cik"],
            name=company_dict["name"],
            year=company_dict["year"],
            quarters=[curr_quarter],
        )
        add_company(
            db=db,
            company_data=company_obj.dict(by_alias=True),
            company_collection=company_collection,
        )
        celery_log.info("Company added succesfully")

    else:
        # add new info if quarter exist and type of filing is new
        db[company_collection].update_one(
            {
                "_id": company_in_db["_id"],
                "quarters.q": {"$eq": curr_quarter.q},
                "quarters.info.type": {"$ne": curr_info.type},
            },
            {"$push": {"quarters.$.info": curr_info.dict()}},
        )

        # push new quarter for company if it does not exist
        db[company_collection].update_one(
            {"_id": company_in_db["_id"], "quarters.q": {"$ne": curr_quarter.q}},
            {"$push": {"quarters": curr_quarter.dict()}},
        )
        celery_log.info("Company info and/or quarter added to company succesfully")

    close_mongo_connection()
    return "Success"
