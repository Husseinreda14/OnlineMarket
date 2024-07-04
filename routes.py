from fastapi import APIRouter
from auth import router as auth_router
from controllers.products import router as products_router 
router = APIRouter()

@router.get("/")
def read_root():
    return {"Hello": "World"}

@router.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}


# Include the auth router
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(products_router, prefix="/products")
