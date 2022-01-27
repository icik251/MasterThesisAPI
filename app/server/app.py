from fastapi import FastAPI
#from app.server.routes.company import router as CompanyRouter

from .routes.company import router as CompanyRouter

app = FastAPI()
app.include_router(CompanyRouter, tags=["Student"], prefix="/student")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to this fantastic app!"}