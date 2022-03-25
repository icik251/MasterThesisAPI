from typing import Optional
from pymongo import MongoClient
from core import settings
from motor.motor_asyncio import AsyncIOMotorClient
import models.stock_price as model_stock_price


def add_stock_prices(
    db: MongoClient,
    stock_prices: list,
    stock_price_collection: str = settings.STOCK_PRICE_COLLECTION,
):
    stock_prices = db[stock_price_collection].insert_many(stock_prices)


def delete_stock_prices(
    db: MongoClient,
    cik: int,
    ts_type: str = "adj_close",
    stock_price_collection: str = settings.STOCK_PRICE_COLLECTION,
):
    res_obj = db[stock_price_collection].delete_many(
        {"metadata.cik": cik, "metadata.ts_type": ts_type}
    )
    return res_obj.acknowledged


async def get_stock_prices(
    db: AsyncIOMotorClient,
    cik: Optional[int] = None,
    ts_type: str = "adj_close",
    stock_price_collection: str = settings.STOCK_PRICE_COLLECTION,
):

    stock_prices_list = []
    if cik:
        async for stock_price_obj in db[stock_price_collection].find(
            {"metadata.cik": cik, "metadata.ts_type": ts_type}
        ).sort("timestamp", 1):
            stock_prices_list.append(model_stock_price.StockPrice(**stock_price_obj))
    else:
        async for stock_price_obj in db[stock_price_collection].find(
            {"metadata.ts_type": ts_type}
        ).sort([("timestamp", 1), ("metadata.cik", 1)]):

            stock_prices_list.append(model_stock_price.StockPrice(**stock_price_obj))

    return stock_prices_list
