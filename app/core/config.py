from pydantic import BaseSettings
import os


class Settings(BaseSettings):
    API_V1_STR: str = os.getenv("API_V1_STR")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME")
    MONGO_DATABASE_URI: str = os.getenv("MONGO_DATABASE_URI")
    MONGODB_NAME: str = os.getenv("MONGODB_NAME")

    GECKODRIVER_PATH: str = os.getenv("GECKODRIVER_PATH")
    PATH_TO_SEARCH_TERMS: str = os.getenv("PATH_TO_SEARCH_TERMS")
    # collections for mongo
    COMPANY_COLLECTION: str = os.getenv("COMPANY_COLLECTION")
    METADATA_COLLECTION: str = os.getenv("METADATA_COLLECTION")
    STOCK_PRICE_COLLECTION: str = os.getenv("STOCK_PRICE_COLLECTION")
    INPUT_DATA_COLLECTION: str = os.getenv("INPUT_DATA_COLLECTION")

    AV_API_KEY: str = os.getenv("AV_API_KEY")

    class Config:
        pass
        # env_file = ""


settings = Settings()
