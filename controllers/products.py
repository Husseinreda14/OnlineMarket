import uuid
from bson import ObjectId
from fastapi import APIRouter, Depends, Form, HTTPException, Query, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime
from auth import SellerAuth
from models import Product
from db import db
import config
import os
from typing import List, Optional

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/create")
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    files: List[UploadFile] = File(...),
    token: str = Depends(oauth2_scheme)
):
    seller_id = await SellerAuth(token)

    image_urls = []
    for file in files:
        # Generate a unique filename using UUID
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join("uploads", "productimages", unique_filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        image_urls.append(unique_filename)  # Store only the filename

    product_dict = {
        "_id": str(ObjectId()),  # Convert ObjectId to string
        "seller_id": seller_id,
        "name": name,
        "description": description,
        "price": price,
        "images": image_urls,
        "created_at": datetime.utcnow()
    }

    await db["products"].insert_one(product_dict)
    return Product(**product_dict)

@router.get("/GetAll" )
async def get_all_products(
    search: Optional[str] = Query(None, description="Search term for name, description, or seller email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, gt=0, le=100, description="Number of products to return per page"),
    sort_by_price: Optional[bool] = Query(None, description="Sort by price if True")
):
    query = {}

    # Search by name, description, or seller email
    if search:
        seller_ids = [user["_id"] for user in await db["users"].find({"email": {"$regex": search, "$options": "i"}}).to_list(length=None)]
        query = {
            "$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"seller_id": {"$in": seller_ids}}
            ]
        }

    sort = [("price", 1)] if sort_by_price else None
    skip = (page - 1) * limit  # Calculate the number of products to skip
    products_cursor = db["products"].find(query).skip(skip).limit(limit)
    if sort:
        products_cursor = products_cursor.sort(sort)

    products = await products_cursor.to_list(length=limit)
    if not products:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found")


    product_responses = []
    for product in products:
        seller = await db["users"].find_one({"_id": product["seller_id"]})
        if not seller:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
        
        product_response = {
            "id": str(product["_id"]),
            "seller_email": seller["email"],
            "name": product["name"],
            "description": product["description"],
            "price": product["price"],
            "images": [f"{config.API_URL}/uploads/productimages/{img}" for img in product["images"]],
            "created_at": product["created_at"]
        }
        product_responses.append(product_response)
    
    return product_responses


@router.get("/GetProduct/{product_id}")
async def get_product(product_id: str):
    product = await db["products"].find_one({"_id": product_id})
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    seller = await db["users"].find_one({"_id": product["seller_id"]})
    if not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    
    product["seller_email"] = seller["email"]
    product["images"] = [f"{config.API_URL}/uploads/productimages/{img}" for img in product["images"]]
    
    product_response = {
        "id": str(product["_id"]),
        "seller_email": seller["email"],
        "name": product["name"],
        "description": product["description"],
        "price": product["price"],
        "images": [f"{config.API_URL}/uploads/productimages/{img}" for img in product["images"]],
        "created_at": product["created_at"]
    }
    return product_response


@router.put("/update/{product_id}")
async def update_product(
    product_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
      files: Optional[List[UploadFile]] = File(None),
    token: str = Depends(oauth2_scheme)
):
    seller_id = await SellerAuth(token)
    product = await db["products"].find_one({"_id": product_id, "seller_id": seller_id})
    if not product:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this product")

    update_data = {}
    if name:
        update_data["name"] = name
    if description:
        update_data["description"] = description
    if price is not None:
        update_data["price"] = price

    if files:
        image_urls = []
        for file in files:
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join("uploads", "productimages", unique_filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            image_urls.append(unique_filename)  # Store only the filename
        update_data["images"] = image_urls

    await db["products"].update_one({"_id": product_id}, {"$set": update_data})
    updated_product = await db["products"].find_one({"_id": product_id})
    return {
        "id": str(updated_product["_id"]),
        "name": updated_product["name"],
        "description": updated_product["description"],
        "price": updated_product["price"],
        "images": [f"{config.API_URL}/uploads/productimages/{img}" for img in updated_product["images"]],
        "created_at": updated_product["created_at"]
    }

@router.delete("/delete/{product_id}")
async def delete_product(
    product_id: str,
    token: str = Depends(oauth2_scheme)
):
    seller_id = await SellerAuth(token)
    product = await db["products"].find_one({"_id": product_id, "seller_id": seller_id})
    if not product:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this product")

    await db["products"].delete_one({"_id":product_id})
    return {"message": "Product deleted successfully"}