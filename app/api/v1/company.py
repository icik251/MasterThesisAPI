from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient

# from crud.company import add_company
from databases.mongodb.session import get_database
from schemas.company import Company, ResponseModel
from celery_worker import create_company

router = APIRouter()


@router.post("/", response_description="Company data added into the database")
def add_company_data(company: Company = Body(...)):
    create_company.delay(company.dict())

    return {"Task added to queue."}


# @router.post("/", response_description="Company data added into the database")
# async def add_company_data(db: AsyncIOMotorClient = Depends(get_database), company: Company = Body(...)):
#     new_company = await add_company(db, company.dict(by_alias=True))

#     return ResponseModel(new_company, "Company added successfully.")

# @app.post('/order')
# def add_order(order: models.Order):
#     # use delay() method to call the celery task
#     create_order.delay(order.customer_name, order.order_quantity)
#     return {"message": "Order Received! Thank you for your patience."}


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
