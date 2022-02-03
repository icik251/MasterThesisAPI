import uvicorn
from fastapi import FastAPI
from api.v1 import api_router
from core import settings
from databases.mongodb.mongo_utils import (
    connect_to_mongo_async,
    close_mongo_connection_async,
)

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix=settings.API_V1_STR)

app.add_event_handler("startup", connect_to_mongo_async)
app.add_event_handler("shutdown", close_mongo_connection_async)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000, reload=False)
