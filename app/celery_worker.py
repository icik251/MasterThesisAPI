# from services.sec_scraper import SECScraper
import copy
import json
from services import process_filing
from services.utils import load_search_terms, requests_get

from crud.company import add_company, get_company
from crud.stock_price import add_stock_prices, delete_stock_prices

from databases.mongodb.session import get_database
from databases.mongodb.mongo_utils import connect_to_mongo, close_mongo_connection

from models.company import Company
from models.quarter import Quarter
from models.stock_price import StockPrice
from models.metadata import Metadata

import celery
from celery.utils.log import get_task_logger

import datetime
import time
from dotenv import load_dotenv
import os

import yfinance as yf


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
    result_extended=True,
)

celery_log = get_task_logger(__name__)


class BaseTaskWithRetry(celery.Task):
    autoretry_for = (Exception,)  # retry for all
    max_retries = 2  # max retries
    retry_backoff = True  # exponential delay


@celery_app.task(name="create_company", base=BaseTaskWithRetry)
def create_company(company_dict: dict):
    list_of_result, company_type = process_filing.logic(
        company_dict["index_url"],
        path_to_search_terms=os.getenv("PATH_TO_SEARCH_TERMS_CELERY"),
    )

    if len(list_of_result) > 1:
        return f"{company_dict.get('cik')} - {company_dict.get('year')} Q-{company_dict.get('quarter')} | List of result contains > 1"

    dict_of_extracted_text, metadata_to_check = list_of_result[0]
    # Check if CIKs differ
    if int(metadata_to_check.sec_cik) != company_dict["cik"]:
        return f"{company_dict.get('cik')} - {company_dict.get('year')} Q-{company_dict.get('quarter')} | Different CIKs {int(metadata_to_check.sec_cik)} and {company_dict.get('cik')}"
    # Check if filing date differ
    metadata_datetime = datetime.datetime.strptime(
        metadata_to_check.sec_filing_date, "%Y%m%d"
    ).isoformat()
    if (
        company_dict.get("filing_date", None)
        and metadata_datetime != company_dict["filing_date"]
    ):
        return f"{company_dict.get('cik')} - {company_dict.get('year')} Q-{company_dict.get('quarter')} | Different filing dates {metadata_datetime} and {company_dict['filing_date']}"

    curr_metadata = Metadata(
        type=metadata_to_check.document_type,  # think if adding type from here is the best
        filing_date=datetime.datetime.strptime(
            metadata_to_check.sec_filing_date, "%Y%m%d"
        ),
        period_of_report=datetime.datetime.strptime(
            metadata_to_check.sec_period_of_report, "%Y%m%d"
        ),
        filing_url=metadata_to_check.sec_url,
        risk_section=dict_of_extracted_text.get("risk_section", None),
        mda_section=dict_of_extracted_text.get("mda_section", None),
        qqd_section=dict_of_extracted_text.get("qqd_section", None),
        company_type=company_type,
    )

    curr_quarter = Quarter(
        q=company_dict["quarter"], metadata=[curr_metadata.dict(by_alias=True)]
    )

    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        if client:
            break
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    company_collection = os.getenv("COMPANY_COLLECTION")

    company_in_db = get_company(
        db=db,
        company_data=company_dict,
        company_collection=company_collection,
    )

    if not company_in_db:
        # initial creation - if company exists only append new quarter, else create new entry
        company_obj = Company(
            cik=company_dict["cik"],
            name=company_dict["name"],
            ticker=company_dict["ticker"],
            year=company_dict["year"],
            quarters=[curr_quarter],
        )
        add_company(
            db=db,
            company_data=company_obj.dict(by_alias=True),
            company_collection=company_collection,
        )
        celery_log.info(
            f"{company_dict.get('cik')} - {company_dict.get('year')} Q-{company_dict.get('quarter')} | Company added successfully"
        )
        close_mongo_connection(client)
        return f"{company_dict.get('cik')} - {company_dict.get('year')} Q-{company_dict.get('quarter')} | Company added successfully"

    else:
        # add new metadata if quarter exist and type of filing is new
        db[company_collection].update_one(
            {
                "_id": company_in_db["_id"],
                "quarters.q": {"$eq": curr_quarter.q},
                # "quarters.metadata.type": {"$ne": curr_metadata.type},
            },
            {
                "$push": {
                    "quarters.$.metadata": {
                        "$each": [curr_metadata.dict(by_alias=True)],
                        "$sort": {"filing_date": 1},
                    }
                }
            },
        )

        # push new quarter for company if it does not exist
        db[company_collection].update_one(
            {"_id": company_in_db["_id"], "quarters.q": {"$ne": curr_quarter.q}},
            {
                "$push": {
                    "quarters": {
                        "$each": [curr_quarter.dict(by_alias=True)],
                        "$sort": {"q": 1},
                    }
                }
            },
        )
        celery_log.info(
            f"{company_dict.get('cik')} - {company_dict.get('year')} Q-{company_dict.get('quarter')} | Company metadata and/or quarter added to company succesfully"
        )
        close_mongo_connection(client)
        return f"{company_dict.get('cik')} - {company_dict.get('year')} Q-{company_dict.get('quarter')} | Company metadata and/or quarter added to company succesfully"


@celery_app.task(name="create_stock_prices", base=BaseTaskWithRetry)
def create_stock_prices(curr_company: dict, start_date: str):
    # connect to DB
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    stock_price_collection = os.getenv("STOCK_PRICE_COLLECTION")

    if not curr_company["ticker"]:
        return f"{curr_company.get('cik')} ticker is {curr_company.get('ticker')} | Ticker does not exist, can't create time-series"

    r = requests_get(
        f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={curr_company['ticker']}&outputsize=full&apikey={os.getenv('AV_API_KEY')}"
    )

    while r.status_code != 200:
        print(f"Status code: {r.status_code}")
        time.sleep(60)
        r = requests_get(
            f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={curr_company['ticker']}&outputsize=full&apikey={os.getenv('AV_API_KEY')}"
        )

    data = r.json()
    stock_prices_dict = data.get("Time Series (Daily)", None)
    if not stock_prices_dict or len(stock_prices_dict) == 0:
        return f"{curr_company.get('cik')} ticker is {curr_company.get('ticker')} | No data for company, can't create time-series"

    # Process start date logic
    list_of_dates = list(stock_prices_dict.keys())

    while start_date not in list_of_dates:
        start_datetime = datetime.datetime.fromisoformat(start_date)
        start_datetime += datetime.timedelta(days=1)
        start_date = start_datetime.strftime("%Y-%m-%d")

    idx = list_of_dates.index(start_date)
    list_of_dates = list_of_dates[: idx + 1]

    list_prices = []
    for date in sorted(list_of_dates):
        curr_data_dict = stock_prices_dict[date]
        stock_price_obj = StockPrice(
            metadata={
                "cik": curr_company["cik"],
                "ticker": curr_company["ticker"],
                "ts_type": "adj_close",
            },
            timestamp=datetime.datetime.fromisoformat(date),
            open=curr_data_dict["1. open"],
            high=curr_data_dict["2. high"],
            low=curr_data_dict["3. low"],
            close=curr_data_dict["4. close"],
            adjusted_close=curr_data_dict["5. adjusted close"],
            volume=curr_data_dict["6. volume"],
            divident_amount=curr_data_dict["7. dividend amount"],
            split_coeff=curr_data_dict["8. split coefficient"],
        )
        list_prices.append(stock_price_obj.dict(by_alias=True))

    # delete old time-series if exists for company
    delete_stock_prices(db, curr_company["cik"], stock_price_collection)
    # add new stock prices
    add_stock_prices(db, list_prices, stock_price_collection)
    close_mongo_connection(client)
    return f"{curr_company.get('cik')} ticker is {curr_company.get('ticker')} | Stock prices added succesfully"
