from pymongo import MongoClient
from core import settings


def add_stock_prices(
    db: MongoClient,
    stock_prices: list,
    stock_price_collection: str = settings.STOCK_PRICE_COLLECTION,
):
    stock_prices = db[stock_price_collection].insert_many(stock_prices)
