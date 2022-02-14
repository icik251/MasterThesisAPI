from typing import Any, Optional
from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from crud.company import get_company_async

# from crud.company import add_company
from schemas.company import Company, ResponseModel, ErrorResponseModel
from celery_worker import create_company
from databases.mongodb.session import get_database_async

router = APIRouter()


@router.post("/", response_description="Company data added into the queue")
def add_company_data(company: Company = Body(...)):
    create_company.delay(company.dict())
    return {"message": "Task added to queue."}


@router.get("/{cik}", response_description="Get data for company")
async def get_company_data(
    cik: int,
    year: Optional[int] = None,
    db: AsyncIOMotorClient = Depends(get_database_async),
):
    company_res = await get_company_async(db, cik, year)
    if company_res:
        return ResponseModel(company_res, "Company retrieved")
    else:
        return ErrorResponseModel("An error occurred.", 404, "Company doesn't exist.")


# @router.post("/", response_description="Company data added into the database")
# async def add_company_data(db: AsyncIOMotorClient = Depends(get_database), company: Company = Body(...)):
#     new_company = await add_company(db, company.dict(by_alias=True))

#     return ResponseModel(new_company, "Company added successfully.")


# EXAMPLE using sqlalchemy

# from typing import Any, List

# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session

# from app import schemas, crud
# from app.api.deps import get_db

# router = APIRouter()


# @router.get("", response_model=List[schemas.ProductResponse])
# def read_products(db: Session = Depends(get_db), skip: int = 0, limit: int = 100) -> Any:
#     """
#     Retrieve all products.
#     """
#     products = crud.product.get_multi(db, skip=skip, limit=limit)
#     return products


# @router.post("", response_model=schemas.ProductResponse)
# def create_product(*, db: Session = Depends(get_db), product_in: schemas.ProductCreate) -> Any:
#     """
#     Create new products.
#     """
#     product = crud.product.create(db, obj_in=product_in)
#     return product


# @router.put("", response_model=schemas.ProductResponse)
# def update_product(*, db: Session = Depends(get_db), product_in: schemas.ProductUpdate) -> Any:
#     """
#     Update existing products.
#     """
#     product = crud.product.get(db, model_id=product_in.id)
#     if not product:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="The product with this ID does not exist in the system.",
#         )
#     product = crud.product.update(db, db_obj=product, obj_in=product_in)
#     return product


# @router.delete("", response_model=schemas.Message)
# def delete_product(*, db: Session = Depends(get_db), id: int) -> Any:
#     """
#     Delete existing product.
#     """
#     product = crud.product.get(db, model_id=id)
#     if not product:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="The product with this ID does not exist in the system.",
#         )
#     crud.product.remove(db, model_id=product.id)
#     return {"message": f"Product with ID = {id} deleted."}
