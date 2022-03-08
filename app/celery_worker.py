# from services.sec_scraper import SECScraper
import copy
import json
from services import process_filing
from services.utils import load_search_terms

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

from datetime import datetime
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
    list_of_result = process_filing.logic(
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
    metadata_datetime = datetime.strptime(
        metadata_to_check.sec_filing_date, "%Y%m%d"
    ).isoformat()
    if (
        company_dict.get("filing_date", None)
        and metadata_datetime != company_dict["filing_date"]
    ):
        return f"{company_dict.get('cik')} - {company_dict.get('year')} Q-{company_dict.get('quarter')} | Different filing dates {metadata_datetime} and {company_dict['filing_date']}"

    curr_metadata = Metadata(
        type=metadata_to_check.document_type,  # think if adding type from here is the best
        filing_date=datetime.strptime(metadata_to_check.sec_filing_date, "%Y%m%d"),
        period_of_report=datetime.strptime(
            metadata_to_check.sec_period_of_report, "%Y%m%d"
        ),
        filing_url=metadata_to_check.sec_url,
        risk_section=dict_of_extracted_text.get("risk_section", None),
        mda_section=dict_of_extracted_text.get("mda_section", None),
        qqd_section=dict_of_extracted_text.get("qqd_section", None),
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
                "quarters.metadata.type": {"$ne": curr_metadata.type},
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


# @celery_app.task(name="create_metadata", base=BaseTaskWithRetry)
# def create_metadata(metadata_dict: dict, curr_company: dict):
#     curr_info = None
#     for quarter_dict in curr_company["quarters"]:
#         if metadata_dict["quarter"] == quarter_dict["q"]:
#             curr_info = quarter_dict["info"][0]

#     if not curr_info:
#         return f"{metadata_dict.get('cik')} - {metadata_dict.get('year')} Q-{metadata_dict.get('quarter')} | Company info does not exist"

#     # connect to DB
#     client = None
#     while not client:
#         client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
#         time.sleep(5)

#     db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
#     metadata_collection = os.getenv("METADATA_COLLECTION")

#     extractorApi = ExtractorApi(os.getenv("SEC_API_KEY"))
#     xbrlApi = XbrlApi(os.getenv("SEC_API_KEY"))

#     mda, risk = None, None
#     # Might change the sections if we cant get a lot of them
#     if "10-Q" in metadata_dict["type"]:
#         mda = extractorApi.get_section(filing_url=curr_info["url_htm"], section="2")
#         risk = extractorApi.get_section(filing_url=curr_info["url_htm"], section="21A")

#     elif "10-K" in metadata_dict["type"]:
#         mda = extractorApi.get_section(filing_url=curr_info["url_htm"], section="7")
#         risk = extractorApi.get_section(filing_url=curr_info["url_htm"], section="1A")

#     if mda == "undefined":
#         mda = None
#     if risk == "undefined":
#         risk = None

#     xbrl_json = xbrlApi.xbrl_to_json(htm_url=curr_info["url_htm"])

#     # Set default values
#     assets, liabilities, liabilities_and_stockholders_equity, dict_of_profit_loss = (
#         [],
#         [],
#         [],
#         {},
#     )
#     if not xbrl_json["status"] == 404:
#         balance_sheets = xbrl_json["BalanceSheets"]
#         statements_of_income = xbrl_json["StatementsOfIncome"]
#         statements_of_cash_flows = xbrl_json["StatementsOfCashFlows"]
#         statements_of_shareholders_equity = xbrl_json["StatementsOfShareholdersEquity"]

#         assets = balance_sheets.get("Assets", [])
#         liabilities = balance_sheets.get("Liabilities", [])
#         liabilities_and_stockholders_equity = balance_sheets.get(
#             "LiabilitiesAndStockholdersEquity", []
#         )

#         dict_of_profit_loss = {}
#         # profitloss
#         dict_of_profit_loss["statements_of_income_pl"] = statements_of_income.get(
#             "ProfitLoss", []
#         )
#         dict_of_profit_loss[
#             "statements_of_cash_flows_pl"
#         ] = statements_of_cash_flows.get("ProfitLoss", [])
#         dict_of_profit_loss[
#             "statements_of_shareholders_equity_pl"
#         ] = statements_of_shareholders_equity.get("ProfitLoss", [])
#         # netincodeloss
#         dict_of_profit_loss["statements_of_income_ni"] = statements_of_income.get(
#             "NetIncomeLoss", []
#         )
#         dict_of_profit_loss[
#             "statements_of_cash_flows_ni"
#         ] = statements_of_cash_flows.get("NetIncomeLoss", [])
#         dict_of_profit_loss[
#             "statements_of_shareholders_equity_ni"
#         ] = statements_of_shareholders_equity.get("NetIncomeLoss", [])
#     # dict_of_revenues = {}
#     # dict_of_revenues['statements_of_income'] = statements_of_income.get("Revenues", None)
#     # dict_of_revenues['statements_of_cash_flows'] = statements_of_cash_flows.get("Revenues", None)
#     # dict_of_revenues['statements_of_shareholders_equity'] = statements_of_shareholders_equity.get("Revenues", None)

#     curr_metadata = Metadata(
#         cik=metadata_dict["cik"],
#         year=metadata_dict["year"],
#         quarter=metadata_dict["quarter"],
#         type=metadata_dict["type"],
#         mda_section=mda,
#         risk_section=risk,
#         assets=assets,
#         liabilities=liabilities,
#         liabilities_and_stockholders_equity=liabilities_and_stockholders_equity,
#         profit_loss=dict_of_profit_loss,
#     )

#     add_metadata(db, curr_metadata.dict(by_alias=True), metadata_collection)
#     close_mongo_connection(client)
#     return f"{metadata_dict.get('cik')} - {metadata_dict.get('year')} Q-{metadata_dict.get('quarter')} | Metadata added succesfully"


@celery_app.task(name="create_stock_prices", base=BaseTaskWithRetry)
def create_stock_prices(curr_company: dict, start_date: str, end_date: str):
    # connect to DB
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    stock_price_collection = os.getenv("STOCK_PRICE_COLLECTION")

    if not curr_company["ticker"]:
        return f"{curr_company.get('cik')} ticker is {curr_company.get('ticker')} | Ticker does not exist, can't create time-series"

    stock_df = yf.download(curr_company["ticker"], start=start_date, end=end_date)
    stock_df.reset_index(level=0, inplace=True)

    if len(stock_df) == 0:
        return f"{curr_company.get('cik')} ticker is {curr_company.get('ticker')} | No data for company, can't create time-series"

    list_prices = []
    for timestamp, open, high, low, close, adj_close, volume in zip(
        stock_df["Date"].values,
        stock_df["Open"].values,
        stock_df["High"].values,
        stock_df["Low"].values,
        stock_df["Close"].values,
        stock_df["Adj Close"].values,
        stock_df["Volume"].values,
    ):
        stock_price_obj = StockPrice(
            metadata={
                "cik": curr_company["cik"],
                "ticker": curr_company["ticker"],
                "ts_type": "adj_close",
            },
            timestamp=timestamp,
            open=round(open, 4),
            high=round(high, 4),
            low=round(low, 4),
            close=round(close, 4),
            adjusted_close=round(adj_close, 4),
            volume=volume,
        )
        list_prices.append(stock_price_obj.dict(by_alias=True))

    # delete old time-series if exists for company
    delete_stock_prices(db, curr_company["cik"], stock_price_collection)
    # add new stock prices
    add_stock_prices(db, list_prices, stock_price_collection)
    close_mongo_connection(client)
    return f"{curr_company.get('cik')} ticker is {curr_company.get('ticker')} | Stock prices added succesfully"
