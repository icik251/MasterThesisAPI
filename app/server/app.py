from fastapi import FastAPI

from .routes.company import router as CompanyRouter

app = FastAPI()
app.include_router(CompanyRouter, tags=["Company"], prefix="/company")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to this fantastic app!"}