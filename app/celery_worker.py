# from services.sec_scraper import SECScraper
from collections import defaultdict
import copy
import json
import traceback
import random

random.seed(42)
from bson.objectid import ObjectId
from sklearn.model_selection import KFold, StratifiedKFold

from services import (
    process_filing,
    company_input_data_handler,
    company_fundamental_data_handler,
    fundamental_data_handler,
)
from services.utils import load_search_terms, requests_get

from crud.company import add_company, get_company
from crud.stock_price import add_stock_prices, delete_stock_prices
from crud.input_data import (
    add_input_data,
    delete_input_data,
    get_input_data_by_kfold_split_type,
    get_input_data_by_year_q,
    update_input_data_by_id,
    get_input_data_by_cik,
    get_all_input_data,
)
from crud.adapter_data import (
    add_adater_data,
    get_all_adapter_data,
    update_adapter_data_by_id,
)
from crud.fundamental_data import add_fundamental_data, delete_fundamental_data

from databases.mongodb.session import get_database
from databases.mongodb.mongo_utils import connect_to_mongo, close_mongo_connection

from models.company import Company
from models.quarter import Quarter
from models.stock_price import StockPrice
from models.metadata import Metadata
from models.input_data import InputData
from models.storage import Storage
from models.fundamental_data import FundamentalData

import celery
from celery.utils.log import get_task_logger

import datetime
import time
from dotenv import load_dotenv
import os

import numpy as np
import pickle
from sklearn.preprocessing import RobustScaler, StandardScaler, MinMaxScaler

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

import pandas as pd


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
            sector=company_dict["sector"],
            industry=company_dict["industry"],
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
        close_mongo_connection(client)
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
        close_mongo_connection(client)
        return f"{curr_company.get('cik')} ticker is {curr_company.get('ticker')} | No data for company, can't create time-series"

    # Process start date logic
    list_of_dates = list(stock_prices_dict.keys())

    while start_date not in list_of_dates:
        start_datetime = datetime.datetime.fromisoformat(start_date)
        start_datetime += datetime.timedelta(days=1)
        start_date = start_datetime.strftime("%Y-%m-%d")

    idx = list_of_dates.index(start_date)
    list_of_dates = list_of_dates[: idx + 1]

    dict_of_dates_checkers = defaultdict(int)

    list_prices = []
    for date in sorted(list_of_dates):
        dict_of_dates_checkers[date.split("-")[0]] += 1

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

    # ~252 are the official trading days, we set 240
    # threshold_trading_days = 240
    # if (
    #     dict_of_dates_checkers["2017"] < threshold_trading_days
    #     or dict_of_dates_checkers["2018"] < threshold_trading_days
    #     or dict_of_dates_checkers["2019"] < threshold_trading_days
    #     or dict_of_dates_checkers["2020"] < threshold_trading_days
    #     or dict_of_dates_checkers["2021"] < threshold_trading_days
    # ):
    #     close_mongo_connection(client)
    #     return f"{curr_company.get('cik')} ticker is {curr_company.get('ticker')} | Not enough data for company, can't create time-series, \
    #         2017 days: {dict_of_dates_checkers['2017']} | 2018 days: {dict_of_dates_checkers['2018']} | 2019 days: {dict_of_dates_checkers['2019']} | 2020 days: {dict_of_dates_checkers['2020']} | 2021 days: {dict_of_dates_checkers['2021']}"
    # delete old time-series if exists for company

    if not list_prices:
        close_mongo_connection(client)
        return f"{curr_company.get('cik')} ticker is {curr_company.get('ticker')} | Not enough data for company, can't create time-series"

    delete_stock_prices(db, curr_company["cik"], "adj_close", stock_price_collection)
    # add new stock prices
    add_stock_prices(db, list_prices, stock_price_collection)
    close_mongo_connection(client)
    return f"{curr_company.get('cik')} ticker is {curr_company.get('ticker')} | Stock prices added succesfully"


# Comment out if not using the adj inflation creation endpoint to preserve time on initial loading of the API
# import cpi


@celery_app.task(name="create_adj_inflation_stock_prices", base=BaseTaskWithRetry)
def create_adj_inflation_stock_prices(stock_prices_list: list):
    # Logic here
    init_stock_price = None
    list_of_adj_inflation = []
    for idx, curr_stock_price in enumerate(stock_prices_list):
        if idx == 0:
            init_stock_price = curr_stock_price

        try:
            stock_price_obj = StockPrice(
                metadata={
                    "cik": curr_stock_price["metadata"]["cik"],
                    "ticker": curr_stock_price["metadata"]["ticker"],
                    "ts_type": "adj_inflation",
                },
                timestamp=datetime.datetime.fromisoformat(
                    curr_stock_price["timestamp"]
                ),
                open=cpi.inflate(
                    curr_stock_price["open"],
                    datetime.datetime.fromisoformat(curr_stock_price["timestamp"]),
                    to=datetime.datetime.fromisoformat(init_stock_price["timestamp"]),
                    items="Purchasing power of the consumer dollar",
                ),
                high=cpi.inflate(
                    curr_stock_price["high"],
                    datetime.datetime.fromisoformat(curr_stock_price["timestamp"]),
                    to=datetime.datetime.fromisoformat(init_stock_price["timestamp"]),
                    items="Purchasing power of the consumer dollar",
                ),
                low=cpi.inflate(
                    curr_stock_price["low"],
                    datetime.datetime.fromisoformat(curr_stock_price["timestamp"]),
                    to=datetime.datetime.fromisoformat(init_stock_price["timestamp"]),
                    items="Purchasing power of the consumer dollar",
                ),
                close=cpi.inflate(
                    curr_stock_price["close"],
                    datetime.datetime.fromisoformat(curr_stock_price["timestamp"]),
                    to=datetime.datetime.fromisoformat(init_stock_price["timestamp"]),
                    items="Purchasing power of the consumer dollar",
                ),
                adjusted_close=cpi.inflate(
                    curr_stock_price["adjusted_close"],
                    datetime.datetime.fromisoformat(curr_stock_price["timestamp"]),
                    to=datetime.datetime.fromisoformat(init_stock_price["timestamp"]),
                    items="Purchasing power of the consumer dollar",
                ),
                volume=curr_stock_price["volume"],
                divident_amount=curr_stock_price["divident_amount"],
                split_coeff=curr_stock_price["split_coeff"],
            )

            list_of_adj_inflation.append(stock_price_obj.dict(by_alias=True))
        except Exception as e:
            print(e)

    # connect to DB
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    stock_price_collection = os.getenv("STOCK_PRICE_COLLECTION")

    # delete old time-series if exists for company
    delete_stock_prices(
        db, curr_stock_price["metadata"]["cik"], "adj_inflation", stock_price_collection
    )
    # add new stock prices
    add_stock_prices(db, list_of_adj_inflation, stock_price_collection)
    close_mongo_connection(client)
    return f"{curr_stock_price['metadata']['cik']} ticker is {curr_stock_price['metadata']['ticker']} | Adjusted to inflation stock prices added succesfully"


@celery_app.task(name="create_model_input_data", base=BaseTaskWithRetry)
def create_model_input_data(
    company_list: list, stock_prices_list: list, fundamental_data_dict: dict
):
    df_filings_deadlines = pd.read_csv(os.getenv("PATH_TO_FILING_DEADLINES"))
    company_input_data_handler_obj = company_input_data_handler.CompanyInputDataHandler(
        company_list, stock_prices_list, fundamental_data_dict, df_filings_deadlines
    )
    company_input_data_handler_obj.init_prepare_logic()

    # connect to DB
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    input_data_collection = os.getenv("INPUT_DATA_COLLECTION")

    for dict_input in company_input_data_handler_obj.list_of_input_company:
        try:
            input_data_obj = InputData(
                cik=dict_input["cik"],
                sector=dict_input["sector"],
                industry=dict_input["industry"],
                year=dict_input["year"],
                type=dict_input["type"],
                q=dict_input["q"],
                mda_section=dict_input["mda_section"],
                risk_section=dict_input["risk_section"],
                company_type=dict_input["company_type"],
                filing_date=datetime.datetime.fromisoformat(dict_input["filing_date"]),
                deadline_date=dict_input["deadline_date"],
                period_of_report=datetime.datetime.fromisoformat(
                    dict_input["period_of_report"]
                ),
                is_filing_on_time=dict_input["is_filing_on_time"],
                close_price_date=dict_input["close_price_date"],
                close_price=dict_input["close_price"],
                volume=dict_input["volume"],
                close_price_next_date=dict_input["close_price_next_date"],
                close_price_next_day=dict_input["close_price_next_day"],
                volume_next_day=dict_input["volume_next_day"],
                label=dict_input["label"],
                percentage_change=dict_input["percentage_change"],
                k_fold_config=dict_input["k_fold_config"],
                mda_paragraphs=dict_input["mda_paragraphs"],
                mda_sentences=dict_input["mda_sentences"],
                risk_paragraphs=dict_input["risk_paragraphs"],
                risk_sentences=dict_input["risk_sentences"],
                fundamental_data=dict_input["fundamental_data"],
                fundamental_data_imputed_past=dict_input[
                    "fundamental_data_imputed_past"
                ],
            )

            delete_input_data(
                db,
                dict_input["cik"],
                dict_input["year"],
                dict_input["type"],
                dict_input["q"],
                input_data_collection,
            )

            add_input_data(
                db, input_data_obj.dict(by_alias=True), input_data_collection
            )
        except Exception as e:
            print(traceback.format_exc())

    close_mongo_connection(client)
    if company_input_data_handler_obj.list_of_input_company:
        return (
            f"Success for {company_list[0]['cik']} | Model input data added succesfully"
        )
    else:
        return f"Skipping for {company_list[0]['cik']} | Lacking stock prices in the period"


@celery_app.task(name="create_scaled_data_test_set", base=BaseTaskWithRetry)
def create_scaled_data_test_set():
    # connect to DB
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    storage_collection = os.getenv("STORAGE_COLLECTION")
    input_data_collection = os.getenv("INPUT_DATA_COLLECTION")

    list_of_train_input = get_input_data_by_kfold_split_type(
        db=db,
        k_fold=1,
        split_type="train",
        input_data_collection=input_data_collection,
    )
    list_of_val_input = get_input_data_by_kfold_split_type(
        db=db,
        k_fold=1,
        split_type="val",
        input_data_collection=input_data_collection,
    )

    list_of_train_input = list_of_val_input + list_of_train_input

    list_of_test_input = get_input_data_by_kfold_split_type(
        db=db,
        k_fold=1,
        split_type="test",
        input_data_collection=input_data_collection,
    )

    list_of_train_perc_change = [x["percentage_change"] for x in list_of_train_input]
    list_of_test_perc_change = [x["percentage_change"] for x in list_of_test_input]

    scaler_min_max = MinMaxScaler()
    scaler_standard = StandardScaler()
    scaler_robust = RobustScaler()

    # Fit for both scalers
    scaler_min_max.fit(np.array(list_of_train_perc_change).reshape(-1, 1))
    scaler_standard.fit(np.array(list_of_train_perc_change).reshape(-1, 1))
    scaler_robust.fit(np.array(list_of_train_perc_change).reshape(-1, 1))

    # Transform for both scalers
    list_of_train_perc_change_scaled_min_max = scaler_min_max.transform(
        np.array(list_of_train_perc_change).reshape(-1, 1)
    )
    list_of_train_perc_change_scaled_standard = scaler_standard.transform(
        np.array(list_of_train_perc_change).reshape(-1, 1)
    )
    list_of_train_perc_change_scaled_robust = scaler_robust.transform(
        np.array(list_of_train_perc_change).reshape(-1, 1)
    )

    list_of_test_perc_change_scaled_min_max = scaler_min_max.transform(
        np.array(list_of_test_perc_change).reshape(-1, 1)
    )
    list_of_test_perc_change_scaled_standard = scaler_standard.transform(
        np.array(list_of_test_perc_change).reshape(-1, 1)
    )
    list_of_test_perc_change_scaled_robust = scaler_robust.transform(
        np.array(list_of_test_perc_change).reshape(-1, 1)
    )

    # For training
    for idx, (min_max_scaled, standard_scaled, robust_scaled) in enumerate(
        zip(
            list_of_train_perc_change_scaled_min_max,
            list_of_train_perc_change_scaled_standard,
            list_of_train_perc_change_scaled_robust,
        )
    ):
        curr_id = list_of_train_input[idx]["_id"]
        curr_dict_min_max = list_of_train_input[idx]["percentage_change_scaled_min_max"]
        curr_dict_standard = list_of_train_input[idx][
            "percentage_change_scaled_standard"
        ]
        curr_dict_robust = list_of_train_input[idx]["percentage_change_scaled_robust"]

        curr_dict_min_max["full"] = min_max_scaled[0]
        curr_dict_standard["full"] = standard_scaled[0]
        curr_dict_robust["full"] = robust_scaled[0]
        update_query = {
            "percentage_change_scaled_min_max": curr_dict_min_max,
            "percentage_change_scaled_standard": curr_dict_standard,
            "percentage_change_scaled_robust": curr_dict_robust,
        }
        db[input_data_collection].update_one(
            {"_id": curr_id}, {"$set": update_query}, upsert=True
        )

    # For testing
    for idx, (min_max_scaled, standard_scaled, robust_scaled) in enumerate(
        zip(
            list_of_test_perc_change_scaled_min_max,
            list_of_test_perc_change_scaled_standard,
            list_of_test_perc_change_scaled_robust,
        )
    ):
        curr_id = list_of_test_input[idx]["_id"]
        curr_dict_min_max = list_of_test_input[idx]["percentage_change_scaled_min_max"]
        curr_dict_standard = list_of_test_input[idx][
            "percentage_change_scaled_standard"
        ]
        curr_dict_robust = list_of_test_input[idx]["percentage_change_scaled_robust"]

        curr_dict_min_max["full"] = min_max_scaled[0]
        curr_dict_standard["full"] = standard_scaled[0]
        curr_dict_robust["full"] = robust_scaled[0]

        update_query = {
            "percentage_change_scaled_min_max": curr_dict_min_max,
            "percentage_change_scaled_standard": curr_dict_standard,
            "percentage_change_scaled_robust": curr_dict_robust,
        }
        db[input_data_collection].update_one(
            {"_id": curr_id}, {"$set": update_query}, upsert=True
        )

    min_max_scaler_pkl = pickle.dumps(scaler_min_max)
    standard_scaler_pkl = pickle.dumps(scaler_standard)
    robust_scaler_pkl = pickle.dumps(scaler_robust)

    storage_min_max = Storage(
        dumped_object=min_max_scaler_pkl, name="min_max", k_fold="full"
    )
    storage_standard = Storage(
        dumped_object=standard_scaler_pkl, name="standard", k_fold="full"
    )
    storage_robust = Storage(
        dumped_object=robust_scaler_pkl, name="robust", k_fold="full"
    )

    db[storage_collection].insert_one(storage_min_max.dict(by_alias=True))
    db[storage_collection].insert_one(storage_standard.dict(by_alias=True))
    db[storage_collection].insert_one(storage_robust.dict(by_alias=True))

    close_mongo_connection(client)
    return f"Success for k-fold full | Scalers saved and data updated"


@celery_app.task(name="create_scaled_data", base=BaseTaskWithRetry)
def create_scaled_data(k_fold: int):
    # connect to DB
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    storage_collection = os.getenv("STORAGE_COLLECTION")
    input_data_collection = os.getenv("INPUT_DATA_COLLECTION")

    list_of_train_input = get_input_data_by_kfold_split_type(
        db=db,
        k_fold=k_fold,
        split_type="train",
        input_data_collection=input_data_collection,
    )
    list_of_val_input = get_input_data_by_kfold_split_type(
        db=db,
        k_fold=k_fold,
        split_type="val",
        input_data_collection=input_data_collection,
    )

    list_of_train_perc_change = [x["percentage_change"] for x in list_of_train_input]
    list_of_val_perc_change = [x["percentage_change"] for x in list_of_val_input]

    scaler_min_max = MinMaxScaler()
    scaler_standard = StandardScaler()
    scaler_robust = RobustScaler()

    # Fit for ALL scalers
    scaler_min_max.fit(np.array(list_of_train_perc_change).reshape(-1, 1))
    scaler_standard.fit(np.array(list_of_train_perc_change).reshape(-1, 1))
    scaler_robust.fit(np.array(list_of_train_perc_change).reshape(-1, 1))

    # Transform for ALL scalers
    list_of_train_perc_change_scaled_min_max = scaler_min_max.transform(
        np.array(list_of_train_perc_change).reshape(-1, 1)
    )
    list_of_train_perc_change_scaled_standard = scaler_standard.transform(
        np.array(list_of_train_perc_change).reshape(-1, 1)
    )
    list_of_train_perc_change_scaled_robust = scaler_robust.transform(
        np.array(list_of_train_perc_change).reshape(-1, 1)
    )

    list_of_val_perc_change_scaled_min_max = scaler_min_max.transform(
        np.array(list_of_val_perc_change).reshape(-1, 1)
    )
    list_of_val_perc_change_scaled_standard = scaler_standard.transform(
        np.array(list_of_val_perc_change).reshape(-1, 1)
    )
    list_of_val_perc_change_scaled_robust = scaler_robust.transform(
        np.array(list_of_val_perc_change).reshape(-1, 1)
    )

    # For training
    for idx, (min_max_scaled, standard_scaled, robust_scaled) in enumerate(
        zip(
            list_of_train_perc_change_scaled_min_max,
            list_of_train_perc_change_scaled_standard,
            list_of_train_perc_change_scaled_robust,
        )
    ):
        curr_id = list_of_train_input[idx]["_id"]
        curr_dict_min_max = list_of_train_input[idx]["percentage_change_scaled_min_max"]
        curr_dict_standard = list_of_train_input[idx][
            "percentage_change_scaled_standard"
        ]
        curr_dict_robust = list_of_train_input[idx]["percentage_change_scaled_robust"]

        curr_dict_min_max[str(k_fold)] = min_max_scaled[0]
        curr_dict_standard[str(k_fold)] = standard_scaled[0]
        curr_dict_robust[str(k_fold)] = robust_scaled[0]
        update_query = {
            "percentage_change_scaled_min_max": curr_dict_min_max,
            "percentage_change_scaled_standard": curr_dict_standard,
            "percentage_change_scaled_robust": curr_dict_robust,
        }
        db[input_data_collection].update_one(
            {"_id": curr_id}, {"$set": update_query}, upsert=True
        )

    # For validation
    for idx, (min_max_scaled, standard_scaled, robust_scaled) in enumerate(
        zip(
            list_of_val_perc_change_scaled_min_max,
            list_of_val_perc_change_scaled_standard,
            list_of_val_perc_change_scaled_robust,
        )
    ):
        curr_id = list_of_val_input[idx]["_id"]
        curr_dict_min_max = list_of_val_input[idx]["percentage_change_scaled_min_max"]
        curr_dict_standard = list_of_val_input[idx]["percentage_change_scaled_standard"]
        curr_dict_robust = list_of_val_input[idx]["percentage_change_scaled_robust"]

        curr_dict_min_max[str(k_fold)] = min_max_scaled[0]
        curr_dict_standard[str(k_fold)] = standard_scaled[0]
        curr_dict_robust[str(k_fold)] = robust_scaled[0]

        update_query = {
            "percentage_change_scaled_min_max": curr_dict_min_max,
            "percentage_change_scaled_standard": curr_dict_standard,
            "percentage_change_scaled_robust": curr_dict_robust,
        }
        db[input_data_collection].update_one(
            {"_id": curr_id}, {"$set": update_query}, upsert=True
        )

    min_max_scaler_pkl = pickle.dumps(scaler_min_max)
    standard_scaler_pkl = pickle.dumps(scaler_standard)
    robust_scaler_pkl = pickle.dumps(scaler_robust)
    storage_min_max = Storage(
        dumped_object=min_max_scaler_pkl, name="min_max", k_fold=k_fold
    )
    storage_standard = Storage(
        dumped_object=standard_scaler_pkl, name="standard", k_fold=k_fold
    )
    storage_robust = Storage(
        dumped_object=robust_scaler_pkl, name="robust", k_fold=k_fold
    )

    db[storage_collection].insert_one(storage_min_max.dict(by_alias=True))
    db[storage_collection].insert_one(storage_standard.dict(by_alias=True))
    db[storage_collection].insert_one(storage_robust.dict(by_alias=True))

    close_mongo_connection(client)

    return f"Success for k-fold {k_fold} | Scalers saved and data updated"


@celery_app.task(name="create_scaled_data_features", base=BaseTaskWithRetry)
def create_scaled_data_features(
    k_fold: int,
    list_of_features_to_scale: list,
    features_name: str
):
    # connect to DB
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    storage_collection = os.getenv("STORAGE_COLLECTION")
    input_data_collection = os.getenv("INPUT_DATA_COLLECTION")

    list_of_train_input = get_input_data_by_kfold_split_type(
        db=db,
        k_fold=k_fold,
        split_type="train",
        input_data_collection=input_data_collection,
    )

    list_of_val_input = get_input_data_by_kfold_split_type(
        db=db,
        k_fold=k_fold,
        split_type="val",
        input_data_collection=input_data_collection,
    )

    # Grab initially the keys
    list_of_keys = list(list_of_train_input[0][list_of_features_to_scale[0]].keys())

    # Add everything for training
    list_of_train_features = []
    for sample in list_of_train_input:
        curr_sample_features = []
        for feature_key in list_of_features_to_scale:
            for kpi_key in list_of_keys:
                curr_feature_val = sample[feature_key][kpi_key]
                if isinstance(curr_feature_val, float) or isinstance(curr_feature_val, int):
                    curr_sample_features.append(curr_feature_val)
                elif isinstance(curr_feature_val, dict):
                    curr_sample_features.append(curr_feature_val["median"])

        list_of_train_features.append(curr_sample_features)

    # Add everything for validation
    list_of_val_features = []
    for sample in list_of_val_input:
        curr_sample_features = []
        for feature_key in list_of_features_to_scale:
            for kpi_key in list_of_keys:
                curr_feature_val = sample[feature_key][kpi_key]
                if isinstance(curr_feature_val, float) or isinstance(curr_feature_val, int):
                    curr_sample_features.append(curr_feature_val)
                elif isinstance(curr_feature_val, dict):
                    curr_sample_features.append(curr_feature_val["median"])
                
        list_of_val_features.append(curr_sample_features)

    scaler_min_max = MinMaxScaler()
    scaler_standard = StandardScaler()
    scaler_robust = RobustScaler()

    # Fit for ALL scalers
    scaler_min_max.fit(np.array(list_of_train_features))
    scaler_standard.fit(np.array(list_of_train_features))
    scaler_robust.fit(np.array(list_of_train_features))

    # Transform for ALL scalers
    list_of_train_features_scaled_min_max = scaler_min_max.transform(
        np.array(list_of_train_features)
    )
    list_of_train_features_scaled_standard = scaler_standard.transform(
        np.array(list_of_train_features)
    )
    list_of_train_features_scaled_robust = scaler_robust.transform(
        np.array(list_of_train_features)
    )

    list_of_val_features_scaled_min_max = scaler_min_max.transform(
        np.array(list_of_val_features)
    )
    list_of_val_features_scaled_standard = scaler_standard.transform(
        np.array(list_of_val_features)
    )
    list_of_val_features_scaled_robust = scaler_robust.transform(
        np.array(list_of_val_features)
    )

    # For training
    for idx, (min_max_scaled, standard_scaled, robust_scaled) in enumerate(
        zip(
            list_of_train_features_scaled_min_max,
            list_of_train_features_scaled_standard,
            list_of_train_features_scaled_robust,
        )
    ):
        curr_id = list_of_train_input[idx]["_id"]
        curr_dict_min_max = list_of_train_input[idx].get(f"{features_name}_features_scaled_min_max", {})
        curr_dict_standard = list_of_train_input[idx].get(
            f"{features_name}_features_scaled_standard", {}
        )
        curr_dict_robust = list_of_train_input[idx].get(f"{features_name}_features_scaled_robust", {})

        curr_dict_min_max[str(k_fold)] = min_max_scaled.tolist()
        curr_dict_standard[str(k_fold)] = standard_scaled.tolist()
        curr_dict_robust[str(k_fold)] = robust_scaled.tolist()
        update_query = {
            f"{features_name}_features_scaled_min_max": curr_dict_min_max,
            f"{features_name}_features_scaled_standard": curr_dict_standard,
            f"{features_name}_features_scaled_robust": curr_dict_robust,
        }
        db[input_data_collection].update_one(
            {"_id": curr_id}, {"$set": update_query}, upsert=True
        )

    # For validation
    for idx, (min_max_scaled, standard_scaled, robust_scaled) in enumerate(
        zip(
            list_of_val_features_scaled_min_max,
            list_of_val_features_scaled_standard,
            list_of_val_features_scaled_robust,
        )
    ):
        curr_id = list_of_val_input[idx]["_id"]
        curr_dict_min_max = list_of_val_input[idx].get(f"{features_name}_features_scaled_min_max", {})
        curr_dict_standard = list_of_val_input[idx].get(f"{features_name}_features_scaled_standard", {})
        curr_dict_robust = list_of_val_input[idx].get(f"{features_name}_features_scaled_robust", {})

        curr_dict_min_max[str(k_fold)] = min_max_scaled.tolist()
        curr_dict_standard[str(k_fold)] = standard_scaled.tolist()
        curr_dict_robust[str(k_fold)] = robust_scaled.tolist()

        update_query = {
            f"{features_name}_features_scaled_min_max": curr_dict_min_max,
            f"{features_name}_features_scaled_standard": curr_dict_standard,
            f"{features_name}_features_scaled_robust": curr_dict_robust,
        }
        db[input_data_collection].update_one(
            {"_id": curr_id}, {"$set": update_query}, upsert=True
        )

    min_max_scaler_pkl = pickle.dumps(scaler_min_max)
    standard_scaler_pkl = pickle.dumps(scaler_standard)
    robust_scaler_pkl = pickle.dumps(scaler_robust)
    storage_min_max = Storage(
        dumped_object=min_max_scaler_pkl, name=f"{features_name}_features_min_max", k_fold=k_fold
    )
    storage_standard = Storage(
        dumped_object=standard_scaler_pkl, name=f"{features_name}_features_standard", k_fold=k_fold
    )
    storage_robust = Storage(
        dumped_object=robust_scaler_pkl, name=f"{features_name}_features_robust", k_fold=k_fold
    )

    db[storage_collection].insert_one(storage_min_max.dict(by_alias=True))
    db[storage_collection].insert_one(storage_standard.dict(by_alias=True))
    db[storage_collection].insert_one(storage_robust.dict(by_alias=True))

    close_mongo_connection(client)

    return f"Success for k-fold {k_fold} for features {list_of_features_to_scale}, name: {features_name} | Scalers saved and data updated"


@celery_app.task(name="create_scaled_data_features_test_set", base=BaseTaskWithRetry)
def create_scaled_data_features_test_set(
    k_fold: int,
    list_of_features_to_scale: list,
):
    pass


@celery_app.task(name="create_adversarial_sentences", base=BaseTaskWithRetry)
def create_adversarial_sentences(dict_of_sentiment_sentences: dict):
    
    list_of_positive_adv_sentences = []
    list_of_negative_adv_sentences = []
    
    for k, v in dict_of_sentiment_sentences.items():
        if k == "positive":
            list_of_positive_adv_sentences.append(v)
        elif k == "negative":
            list_of_negative_adv_sentences.append(v)
    
    # connect to DB
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    input_data_collection = os.getenv("INPUT_DATA_COLLECTION")
    
    list_of_input_data = get_all_input_data(db=db, input_data_collection=input_data_collection)
    list_of_train_val_corpus = []
    list_of_test_corpus = []
    
    for sample in list_of_input_data:
        if sample["k_fold_config"]["1"] == "test":
            list_of_test_corpus.append(sample)
        else:
            list_of_train_val_corpus.append(sample)
            
    # Process train/val corpus, get 3rd std and add adversarial samples to it.
    robust_percentage_change_train_val = [item["percentage_change_scaled_robust"]["full"] for item in list_of_train_val_corpus]
    list_of_train_val_ids = [item["_id"] for item in list_of_train_val_corpus]
    np_robust_percentage_change_train_val = np.array(robust_percentage_change_train_val)
    train_mean = np.mean(np_robust_percentage_change_train_val)
    train_standard_deviation = np.std(np_robust_percentage_change_train_val)
    train_distance_from_mean = abs(np_robust_percentage_change_train_val - train_mean)
    max_deviations = 3
    train_not_outlier = train_distance_from_mean < max_deviations * train_standard_deviation
    train_no_outliers3 = np_robust_percentage_change_train_val[train_not_outlier]
    
    count_adv_samples = 0
    for item in np_robust_percentage_change_train_val:
        idx_of_id = robust_percentage_change_train_val.index(item)
        curr_sample_id = list_of_train_val_ids[idx_of_id]
        if item not in train_no_outliers3:
            # add adversarial
            if item > 0:
                update_input_data_by_id(db=db, _id=curr_sample_id, dict_of_new_field={"adversarial_samples": list_of_positive_adv_sentences}, input_data_collection=input_data_collection)
            else:
                update_input_data_by_id(db=db, _id=curr_sample_id, dict_of_new_field={"adversarial_samples": list_of_negative_adv_sentences}, input_data_collection=input_data_collection)
            count_adv_samples += 1        
        else:
            # add empty string
            update_input_data_by_id(db=db, _id=curr_sample_id, dict_of_new_field={"adversarial_samples": []}, input_data_collection=input_data_collection)
            
    # Process test corpus, get 1st std and add adversarial samples to it.
    robust_percentage_change_test = [item["percentage_change_scaled_robust"]["full"] for item in list_of_test_corpus]
    list_of_test_ids = [item["_id"] for item in list_of_test_corpus]
    np_robust_percentage_change_test = np.array(robust_percentage_change_test)
    test_mean = np.mean(np_robust_percentage_change_test)
    test_standard_deviation = np.std(np_robust_percentage_change_test)
    test_distance_from_mean = abs(np_robust_percentage_change_test - test_mean)
    max_deviations = 1
    test_not_outlier = test_distance_from_mean < max_deviations * test_standard_deviation
    test_no_outliers1 = np_robust_percentage_change_test[test_not_outlier]
    randomly_sampled_from_test = random.sample(list(test_no_outliers1), count_adv_samples)
    
    for item in np_robust_percentage_change_test:
        idx_of_id = robust_percentage_change_test.index(item)
        curr_sample_id = list_of_test_ids[idx_of_id]
        if item in randomly_sampled_from_test:
            # add adversarial
            # Reverse pos negative for more confusion
            if item > 0:
                update_input_data_by_id(db=db, _id=curr_sample_id, dict_of_new_field={"adversarial_samples": list_of_negative_adv_sentences}, input_data_collection=input_data_collection)
            else:
                update_input_data_by_id(db=db, _id=curr_sample_id, dict_of_new_field={"adversarial_samples": list_of_positive_adv_sentences}, input_data_collection=input_data_collection)
        else:
            # add empty string
            update_input_data_by_id(db=db, _id=curr_sample_id, dict_of_new_field={"adversarial_samples": []}, input_data_collection=input_data_collection)
    

@celery_app.task(name="create_fundamental_data", base=BaseTaskWithRetry)
def create_fundamental_data(cik: int, ticker: str):
    r = requests_get(
        f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={os.getenv('AV_API_KEY')}"
    )
    data_income_statements = r.json()
    r = requests_get(
        f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={os.getenv('AV_API_KEY')}"
    )
    data_balance_sheets = r.json()
    r = requests_get(
        f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={os.getenv('AV_API_KEY')}"
    )
    data_cash_flows = r.json()

    data_handler_obj = company_fundamental_data_handler.CompanyFundamentalDataHandler()
    processed_income_statements = data_handler_obj.process_data(
        data_income_statements["quarterlyReports"]
    )
    processed_balance_sheets = data_handler_obj.process_data(
        data_balance_sheets["quarterlyReports"]
    )
    processed_cash_flows = data_handler_obj.process_data(
        data_cash_flows["quarterlyReports"]
    )

    fundamental_data_dict = FundamentalData(
        cik=cik,
        ticker=ticker,
        balance_sheets=processed_balance_sheets,
        income_statements=processed_income_statements,
        cash_flows=processed_cash_flows,
    )

    # connect to DB
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    fundamental_data_collection = os.getenv("FUNDAMENTAL_DATA_COLLECTION")

    delete_fundamental_data(db, cik, fundamental_data_collection)
    add_fundamental_data(
        db, fundamental_data_dict.dict(by_alias=True), fundamental_data_collection
    )

    close_mongo_connection(client)

    return f"Successfuly added fundamental data for cik: {cik}"


@celery_app.task(name="impute_missing_fundamental_data_by_knn", base=BaseTaskWithRetry)
def impute_missing_fundamental_data_by_knn(year: int, q: int, n_neighbours=1):
    # connect to DB
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    input_data_collection = os.getenv("INPUT_DATA_COLLECTION")

    list_of_input_data = get_input_data_by_year_q(
        db=db, year=year, q=q, input_data_collection=input_data_collection
    )

    if not list_of_input_data:
        return f"No data for year {year} q {q}."

    fundamental_data_handler_obj = fundamental_data_handler.FundamentalDataHandler()
    list_of_problem_industries = []
    for (
        curr_id,
        curr_dict_of_fundamental_data_full,
    ) in fundamental_data_handler_obj.knn_imputer_logic(
        list_of_input_data, n_neighbours
    ):
        if curr_dict_of_fundamental_data_full:
            # Update for curr input data
            update_input_data_by_id(
                db=db,
                _id=ObjectId(curr_id),
                dict_of_new_field={
                    "fundamental_data_imputed_full": curr_dict_of_fundamental_data_full
                },
                input_data_collection=input_data_collection,
            )
        else:
            list_of_problem_industries.append(curr_id)

    close_mongo_connection(client)
    if list_of_problem_industries:
        return f"Successful KNN imputation for fundamental data for year: {year}, q: {q} | Problematic industries: {', '.join(list_of_problem_industries)}"
    else:
        return (
            f"Successful KNN imputation for fundamental data for year: {year}, q: {q}"
        )


@celery_app.task(name="average_fundamental_data", base=BaseTaskWithRetry)
def average_fundamental_data(year: int, q: int):
    # connect to DB
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    input_data_collection = os.getenv("INPUT_DATA_COLLECTION")

    list_of_input_data = get_input_data_by_year_q(
        db=db, year=year, q=q, input_data_collection=input_data_collection
    )

    if not list_of_input_data:
        return f"No data for year {year} q {q}."

    dict_of_fund_data_avg = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for input_data in list_of_input_data:
        for kpi_k, value in input_data["fundamental_data_imputed_full"].items():

            # add for all
            dict_of_fund_data_avg[input_data["industry"]][kpi_k]["count_all"] += 1

            # add if not on time
            if not input_data["is_filing_on_time"]:
                dict_of_fund_data_avg[input_data["industry"]][kpi_k][
                    "count_not_on_time"
                ] += 1
                continue

            dict_of_fund_data_avg[input_data["industry"]][kpi_k]["count_used"] += 1
            dict_of_fund_data_avg[input_data["industry"]][kpi_k]["sum"] += value
            if dict_of_fund_data_avg[input_data["industry"]][kpi_k].get(
                "values_list", None
            ):
                dict_of_fund_data_avg[input_data["industry"]][kpi_k][
                    "values_list"
                ].append(value)
            else:
                dict_of_fund_data_avg[input_data["industry"]][kpi_k]["values_list"] = [
                    value
                ]

    # Calculate average and median
    for industry, kpi_dict in dict_of_fund_data_avg.items():
        for kpi_k, info_dict in kpi_dict.items():
            try:
                dict_of_fund_data_avg[industry][kpi_k]["mean"] = (
                    info_dict["sum"] / info_dict["count_used"]
                )
            except ZeroDivisionError:
                dict_of_fund_data_avg[industry][kpi_k]["mean"] = None

            if info_dict["count_used"] > 0:
                dict_of_fund_data_avg[industry][kpi_k]["median"] = np.median(
                    dict_of_fund_data_avg[industry][kpi_k]["values_list"]
                )
            else:
                dict_of_fund_data_avg[industry][kpi_k]["median"] = None

    for input_data in list_of_input_data:
        curr_industry_dict_of_average = dict_of_fund_data_avg[input_data["industry"]]
        # Update for curr input data
        update_input_data_by_id(
            db=db,
            _id=input_data["_id"],
            dict_of_new_field={"fundamental_data_avg": curr_industry_dict_of_average},
            input_data_collection=input_data_collection,
        )

    close_mongo_connection(client)
    return f"Successfuly calculating average and median fundamental data for year: {year}, q: {q}"


@celery_app.task(name="feature_enginnering", base=BaseTaskWithRetry)
def feature_enginnering(cik: int):
    # connect to DB
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    input_data_collection = os.getenv("INPUT_DATA_COLLECTION")

    list_of_cik_input_data = get_input_data_by_cik(
        db=db, cik=cik, input_data_collection=input_data_collection
    )

    if not list_of_cik_input_data:
        return f"No data for cik {cik}."

    fundamental_data_handler_obj = fundamental_data_handler.FundamentalDataHandler()

    for idx in range(len(list_of_cik_input_data)):
        curr_id = list_of_cik_input_data[idx]["_id"]
        if idx == 0:
            input_data_t = list_of_cik_input_data[idx]
            input_data_t_1 = {}
            input_data_t_2 = {}
        elif idx == 1:
            input_data_t = list_of_cik_input_data[idx]
            input_data_t_1 = list_of_cik_input_data[idx - 1]
            input_data_t_2 = {}
        else:
            input_data_t = list_of_cik_input_data[idx]
            input_data_t_1 = list_of_cik_input_data[idx - 1]
            input_data_t_2 = list_of_cik_input_data[idx - 2]

        list_of_res_dicts = (
            fundamental_data_handler_obj.calculate_difference_for_company_for_timestamp(
                input_data_t, input_data_t_1, input_data_t_2
            )
        )

        for name, diff_dict in list_of_res_dicts:
            update_input_data_by_id(
                db=db,
                _id=curr_id,
                dict_of_new_field={name: diff_dict},
                input_data_collection=input_data_collection,
            )

    close_mongo_connection(client)
    return f"Successfuly feature engineering for cik {cik}"


@celery_app.task(name="k_folds_config", base=BaseTaskWithRetry)
def create_k_folds(k_folds: int):
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    input_data_collection = os.getenv("INPUT_DATA_COLLECTION")

    list_of_input_data = get_all_input_data(
        db=db, is_used=True, input_data_collection=input_data_collection
    )

    list_of_input_data_train_val_corpus = []
    list_of_input_data_test_corpus = []
    for input_data in list_of_input_data:
        if input_data["year"] != 2021:
            list_of_input_data_train_val_corpus.append(input_data)
        else:
            list_of_input_data_test_corpus.append(input_data)

    # Create k_folds for train val
    k_fold_obj = KFold(k_folds, random_state=42, shuffle=True)
    # group_k_fold.get_n_splits(list_of_input_data_train_val_corpus)

    for k_fold_idx, (train_index, val_index) in enumerate(
        k_fold_obj.split(list_of_input_data_train_val_corpus)
    ):
        for idx in train_index:
            list_of_input_data_train_val_corpus[idx]["k_fold_config"][
                str(k_fold_idx + 1)
            ] = "train"
        for idx in val_index:
            list_of_input_data_train_val_corpus[idx]["k_fold_config"][
                str(k_fold_idx + 1)
            ] = "val"

    list_test_keys = list(range(1, k_folds + 1))
    list_test_keys = [str(k) for k in list_test_keys]
    k_fold_config_test = dict(zip(list_test_keys, ["test"] * k_folds))

    # Update for test
    for input_data in list_of_input_data_test_corpus:
        update_input_data_by_id(
            db=db,
            _id=input_data["_id"],
            dict_of_new_field={"k_fold_config": k_fold_config_test},
            input_data_collection=input_data_collection,
        )

    for input_data in list_of_input_data_train_val_corpus:
        update_input_data_by_id(
            db=db,
            _id=input_data["_id"],
            dict_of_new_field={"k_fold_config": input_data["k_fold_config"]},
            input_data_collection=input_data_collection,
        )

    close_mongo_connection(client)
    return f"Successfuly creation of k_folds"


@celery_app.task(name="k_folds_config_adapter", base=BaseTaskWithRetry)
def create_k_folds_adapter(k_folds: int):
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    adapter_data_collection = os.getenv("ADAPTER_DATA_COLLECTION")

    list_of_adapter_data = get_all_adapter_data(
        db=db, adapter_data_collection=adapter_data_collection
    )
    list_of_adapter_y = [x["label"] for x in list_of_adapter_data]

    # Create k_folds for train val
    k_fold_obj = StratifiedKFold(k_folds, random_state=42, shuffle=True)

    for k_fold_idx, (train_index, val_index) in enumerate(
        k_fold_obj.split(list_of_adapter_data, list_of_adapter_y)
    ):
        for idx in train_index:
            list_of_adapter_data[idx]["k_fold_config"][str(k_fold_idx + 1)] = "train"
        for idx in val_index:
            list_of_adapter_data[idx]["k_fold_config"][str(k_fold_idx + 1)] = "val"

    for adapter_data in list_of_adapter_data:
        update_adapter_data_by_id(
            db=db,
            _id=adapter_data["_id"],
            dict_of_new_field={"k_fold_config": adapter_data["k_fold_config"]},
            adapter_data_collection=adapter_data_collection,
        )

    close_mongo_connection(client)
    return f"Successfuly creation of k_folds for Adapter"


@celery_app.task(name="create_adapter_data", base=BaseTaskWithRetry)
def create_adapter_data(adater_data: dict):
    client = None
    while not client:
        client = connect_to_mongo(os.getenv("MONGO_DATABASE_URI"))
        time.sleep(5)

    db = get_database(client, db_name=os.getenv("MONGODB_NAME"))
    adapter_data_collection = os.getenv("ADAPTER_DATA_COLLECTION")

    add_adater_data(db, adater_data, adapter_data_collection)

    close_mongo_connection(client)
    return f"Successfully added adapter data sample"
