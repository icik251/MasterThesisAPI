from fastapi import APIRouter, Body
from schemas.k_folds import KFolds
from schemas.adapter_data import AdapterData, ResponseModel
from celery_worker import create_adapter_data, create_k_folds_adapter
router = APIRouter()


@router.post("/", response_description="Add new sample for adapter dataset")
def add_adapter_data(adapter_data: AdapterData = Body(...)):
    create_adapter_data.delay(adapter_data.dict())
    return ResponseModel([], "Task added to queue")

@router.post("/k_folds/", response_description="Create k_folds by num of k-folds")
async def k_folds_creation(k_folds_post: KFolds = Body(...)):
    k_folds_dict = k_folds_post.dict()
    create_k_folds_adapter.delay(k_folds_dict["k_folds"])
    return ResponseModel([], "Task added to queue.")
