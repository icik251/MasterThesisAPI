"""
    This file is serving as testing and trying MongoDB commands    
"""


from services.sec_scraper import SECScraper
from utils import quarter_exist
from crud.company import add_company, get_company

from databases.mongodb.session import get_database
from databases.mongodb.mongo_utils import connect_to_mongo, close_mongo_connection

from models.company import Company
from models.info import Info
from models.quarter import Quarter

from datetime import datetime
from dotenv import load_dotenv
import os


def check_update(company_dict):
    connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))

    db = get_database(db_name=os.getenv("MONGODB_NAME"))
    company_collection = os.getenv("COMPANY_COLLECTION")

    company_in_db = get_company(
        db=db,
        company_data=company_dict,
        company_collection=company_collection,
    )

    sec_scraper_obj = SECScraper(
        company_dict,
        geckodriver_path="D:\PythonProjects\MasterThesisAPI\geckodriver.exe",
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

    close_mongo_connection()


check_update(
    {
        "cik": 1000045,
        "name": "Nicholas Financial Inc",
        "year": 2020,
        "quarter": 1,
        "type": "10-Q",
        "filing_date": "0020-05-02T00:00:00",
        "html_path": "edgar/data/1000623/0001000623-20-000120-index.html",
    }
)
