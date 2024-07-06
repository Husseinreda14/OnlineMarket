from fastapi import APIRouter
from auth import router as auth_router
from controllers.products import router as products_router 
from controllers.shoppingCart import router as shoppingCart_router
from controllers.orders import router as orders_router
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
router.include_router(shoppingCart_router, prefix="/carts")
router.include_router(orders_router, prefix="/orders")