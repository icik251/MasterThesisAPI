from collections import defaultdict
from typing import Optional
from urllib import response
from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient

from bson.objectid import ObjectId
from utils import parse_model_to_dict, verify_fundamental_data_features
from databases.mongodb.session import get_database_async

from crud.company import get_company_async
from crud.stock_price import get_stock_prices
from crud.fundamental_data import get_fundamental_data_async
from crud.input_data import (
    get_input_data_by_year_q_async,
    update_many_input_data_by_industry,
    update_many_input_data_by_year_q,
    update_many_input_data_by_cik,
    async_get_all_input_data,
    async_update_input_data_by_id,
)

from schemas.input_data import InputData, ResponseModel, ErrorResponseModel
from schemas.scaler import Scaler
from schemas.k_folds import KFolds
from schemas.adversarial_sentences import AdversarialSentences

from models.input_data import UpdateIsIsedInputData

from celery_worker import (
    create_model_input_data,
    create_scaled_data,
    create_k_folds,
    create_scaled_data_test_set,
    create_scaled_data_features,
    create_scaled_data_features_test_set,
    create_adversarial_sentences,
)

router = APIRouter()


@router.post(
    "/", response_description="Reformating and adding model input data to the database"
)
async def add_model_input_data(
    cik_post: InputData = Body(...),
    db: AsyncIOMotorClient = Depends(get_database_async),
):
    cik_dict = cik_post.dict()
    company_list = await get_company_async(db, cik_dict["cik"])
    stock_prices_list = await get_stock_prices(db, cik_dict["cik"], "adj_inflation")
    fundamental_data_dict = await get_fundamental_data_async(db, cik_dict["cik"])

    if company_list and stock_prices_list and fundamental_data_dict:
        # Passing list of company objects
        for idx, company_list_model in enumerate(company_list):
            company_list[idx] = parse_model_to_dict(company_list_model)
        for idx, stock_price_model in enumerate(stock_prices_list):
            stock_prices_list[idx] = parse_model_to_dict(stock_price_model)
        fundamental_data_dict = parse_model_to_dict(fundamental_data_dict)

        create_model_input_data.delay(
            company_list, stock_prices_list, fundamental_data_dict
        )
        return ResponseModel([], "Task added to queue.")
    else:
        return ErrorResponseModel(
            "An error occurred.",
            404,
            "Company doesn't exist or stock prices for inflation are not added or fundamental data is not added. Therefore model input data can't be added.",
        )


@router.get("/{year}/{q}", response_description="Get input data for year and quarter")
async def get_input_data(
    year: int = 2017,
    q: int = 1,
    is_used: Optional[bool] = True,
    db: AsyncIOMotorClient = Depends(get_database_async),
):

    list_of_input_data = await get_input_data_by_year_q_async(
        db, year, q, is_used, True
    )
    if list_of_input_data:
        return ResponseModel(list_of_input_data, "Result retrieved")
    else:
        return ErrorResponseModel(
            "An error occurred.", 404, f"No input data for {year}, {q}"
        )


@router.post(
    "/scaling_labels/", response_description="Scale label data from a certain k-fold"
)
async def scale_data(scaler_post: Scaler = Body(...)):
    scaled_dict = scaler_post.dict()
    create_scaled_data.delay(scaled_dict["k_fold"])
    return ResponseModel([], "Task added to queue.")


@router.post(
    "/scaling_labels_test/",
    response_description="Scale label data for test set using full data",
)
async def scale_data_test():
    create_scaled_data_test_set.delay()
    return ResponseModel([], "Task added to queue.")


@router.post(
    "/scaling_features/",
    response_description="Scale features data from a certain k-fold",
)
async def scale_data(scaler_post: Scaler = Body(...)):
    scaled_dict = scaler_post.dict()
    create_scaled_data_features.delay(
        scaled_dict["k_fold"],
        scaled_dict["list_of_features_to_scale"],
        scaled_dict["features_name"],
    )
    return ResponseModel([], "Task added to queue.")


@router.post(
    "/adversarial_sentences/",
    response_description="Add adversarial sentences to the train/val corpus and also the test set",
)
async def adversarial_sentences(
    adversarial_sentences_post: AdversarialSentences = Body(...),
):
    adversarial_sentences_dict = adversarial_sentences_post.dict()
    create_adversarial_sentences.delay(
        adversarial_sentences_dict["dict_of_sentiment_sentence"]
    )
    return ResponseModel([], "Task added to queue.")


@router.post("/k_folds/", response_description="Create k_folds by num of k-folds")
async def k_folds_creation(k_folds_post: KFolds = Body(...)):
    k_folds_dict = k_folds_post.dict()
    create_k_folds.delay(k_folds_dict["k_folds"])
    return ResponseModel([], "Task added to queue.")


@router.put("/", response_description="Update input data")
async def update_input_is_used(
    industry: Optional[str] = None,
    year: Optional[int] = None,
    q: Optional[int] = None,
    cik: Optional[int] = None,
    _id: Optional[str] = None,
    updated_is_used_input_data: UpdateIsIsedInputData = Body(...),
    db: AsyncIOMotorClient = Depends(get_database_async),
):
    if industry:
        res_list = await update_many_input_data_by_industry(
            db, industry, updated_is_used_input_data.dict()
        )
        return ResponseModel(res_list, f"Succesfully updated for industry {industry}")
    elif year and q:
        res_list = await update_many_input_data_by_year_q(
            db, year, q, updated_is_used_input_data.dict()
        )
        return ResponseModel(
            res_list, f"Succesfully updated for year {year} and quarter {q}"
        )
    elif cik:
        res_list = await update_many_input_data_by_cik(
            db, cik, updated_is_used_input_data.dict()
        )
        return ResponseModel(res_list, f"Succesfully updated for cik {cik}")
    elif _id:
        res = await async_update_input_data_by_id(
            db, ObjectId(_id), updated_is_used_input_data.dict()
        )
        return ResponseModel(res, f"Succesfully updated for _id {_id}")

    elif not industry and not year and not q and not cik and not _id:
        # Go through all input data and decide which to make is_used: "False"
        list_of_input_data = await async_get_all_input_data(db)

        dict_of_lists = defaultdict(list)
        list_of_features_dicts = [
            "fundamental_data_imputed_full",
            "fundamental_data_diff_self_t_1",
            "fundamental_data_diff_self_t_2",
            "fundamental_data_diff_industry_t",
            "fundamental_data_diff_industry_t_1",
            "fundamental_data_diff_industry_t_2",
        ]
        for input_data in list_of_input_data:
            for features_dict in list_of_features_dicts:
                not_size, not_zeros = verify_fundamental_data_features(
                    input_data[features_dict]
                )
                if not not_size or not not_zeros:
                    if str(input_data["_id"]) not in dict_of_lists.keys():
                        await async_update_input_data_by_id(
                            db, input_data["_id"], updated_is_used_input_data.dict()
                        )

                    dict_of_lists[str(input_data["_id"])].append(
                        {features_dict: (not_size, not_zeros)}
                    )
            if (not input_data["label"] or not input_data["percentage_change"]) and str(
                input_data["_id"]
            ) not in dict_of_lists.keys():
                await async_update_input_data_by_id(
                    db, input_data["_id"], updated_is_used_input_data.dict()
                )

        return ResponseModel(dict_of_lists, f"Succesfully updated for all")

    return ErrorResponseModel(
        "Correct data not provided", 412, "No industry or year and q or cik provided"
    )
