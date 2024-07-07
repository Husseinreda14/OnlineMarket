import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from auth import BuyerAuth
from models import ShoppingCart, Product
from db import db
import config
from typing import List, Optional

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/create")
async def add_to_cart(
    request: Request,
    token: str = Depends(oauth2_scheme)
):
    try:
        body = await request.json()
        product_id = body.get("product_id")
        quantity = int(body.get("quantity"))
        user_id = await BuyerAuth(token)
        product = await db["products"].find_one({"_id": product_id, "isDeleted": False})
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if product["quantity"] < quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough product in stock")

        async with await db.client.start_session() as s:
            async with s.start_transaction():
                # Decrement the product quantity
                result = await db["products"].update_one(
                    {"_id": product_id, "quantity": {"$gte": quantity}, "isDeleted": False},
                    {"$inc": {"quantity": -quantity}},
                    session=s
                )
                if result.matched_count == 0:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update product quantity")

                cart_item = await db["shopping_carts"].find_one({"user_id": user_id, "product_id": product_id}, session=s)
                if not cart_item:
                    cart_item = ShoppingCart(
                        user_id=user_id,
                        product_id=product_id,
                        quantity=quantity
                    )
                    await db["shopping_carts"].insert_one(cart_item.dict(by_alias=True), session=s)
                else:
                    return {"message": "Product already added before."}


        return {"message": "Product added to cart successfully"}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")




@router.get("/getmine")
async def get_cart(token: str = Depends(oauth2_scheme)):
    try:
        user_id = await BuyerAuth(token)

        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$lookup": {
                    "from": "products",
                    "localField": "product_id",
                    "foreignField": "_id",
                    "as": "product_details"
                }
            },
            {"$unwind": "$product_details"},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "product_details.seller_id",
                    "foreignField": "_id",
                    "as": "seller_details"
                }
            },
            {"$unwind": "$seller_details"},
            {
                "$project": {
                    "product_id": "$product_details._id",
                    "product_name": "$product_details.name",
                    "seller_email": "$seller_details.email",
                    "quantity": 1,
                    "created_at": 1,
                    "updated_at": 1
                }
            }
        ]

        cart_items = await db["shopping_carts"].aggregate(pipeline).to_list(length=None)

        if not cart_items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        
        return cart_items
    
    except Exception as e:
        print(e)
        raise e



@router.put("/editCart")
async def update_cart(
    request: Request,
    token: str = Depends(oauth2_scheme)
):
    try:
        
        user_id = await BuyerAuth(token)
        body = await request.json()
        product_id = body.get("product_id")
        new_quantity = int(body.get("quantity"))

        if not product_id or new_quantity is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product ID and quantity are required")

        async with await db.client.start_session() as s:
            async with s.start_transaction():
                cart_item = await db["shopping_carts"].find_one({"user_id": user_id, "product_id": product_id}, session=s)
                if not cart_item:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in cart")
                
                product = await db["products"].find_one({"_id":product_id, "isDeleted": False}, session=s)
                if not product:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

                if product["quantity"] + cart_item["quantity"] < new_quantity:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough product in stock")

                # Update product quantity
                updated_product_quantity = product["quantity"] + cart_item["quantity"] - new_quantity
                await db["products"].update_one(
                    {"_id": product_id},
                    {"$set": {"quantity": updated_product_quantity}},
                    session=s
                )

                # Update cart item quantity
                cart_item["quantity"] = new_quantity
                cart_item["updated_at"] = datetime.utcnow()
                await db["shopping_carts"].update_one(
                    {"_id": cart_item["_id"]},
                    {"$set": cart_item},
                    session=s
                )

        return {"message": "Cart updated successfully"}

    except Exception as e:
        await s.abort_transaction()
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")



@router.delete("/removeCart/{product_id}")
async def remove_from_cart(
    product_id: str,
    token: str = Depends(oauth2_scheme)
):
    try:
            
        user_id = await BuyerAuth(token)
        async with await db.client.start_session() as s:
            async with s.start_transaction():
                cart_item = await db["shopping_carts"].find_one({"user_id": user_id, "product_id": product_id}, session=s)
                if not cart_item:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in cart")

                product = await db["products"].find_one({"_id": product_id, "isDeleted": False}, session=s)
                if not product:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

                # Restore the product quantity
                await db["products"].update_one(
                    {"_id":product_id},
                    {"$inc": {"quantity": cart_item["quantity"]}},
                    session=s
                )

                # Remove the cart item
                await db["shopping_carts"].delete_one({"_id": cart_item["_id"]}, session=s)

        return {"message": "Product removed from cart successfully"}

    except Exception as e:
        await s.abort_transaction()
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")
