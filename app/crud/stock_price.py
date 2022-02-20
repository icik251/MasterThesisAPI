from pymongo import MongoClient
from core import settings


def add_stock_prices(
    db: MongoClient,
    stock_prices: list,
    stock_price_collection: str = settings.STOCK_PRICE_COLLECTION,
):
    stock_prices = db[stock_price_collection].insert_many(stock_prices)


def delete_stock_prices(
    db: MongoClient,
    cik: int,
    stock_price_collection: str = settings.STOCK_PRICE_COLLECTION,
):
    res_obj = db[stock_price_collection].delete_many({"metadata.cik": cik})
    return res_obj.acknowledged
