from pydantic import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "MasterThesisAPI"
    MONGO_DATABASE_URI: str = "mongodb://root:root@192.168.239.134:27017"
    MONGODB_NAME: str = "SP500_DB"
    
    # collections for mongo
    COMPANY_COLLECTION = "company"

    class Config:
        env_file = ".env"

settings = Settings()
