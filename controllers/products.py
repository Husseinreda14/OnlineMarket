import uuid
from bson import ObjectId
from fastapi import APIRouter, Depends, Form, HTTPException, Query, status, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from auth import SellerAuth
from models import Product, Log
from db import db
import config
import os
from typing import List, Optional
from apscheduler.schedulers.background import BackgroundScheduler

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper function to log actions
async def log_action(action: str, message: str, success: bool):
    log = Log(action=action, message=message, success=success)
    await db["logs"].insert_one(log.dict(by_alias=True))




@router.post("/create")
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    files: List[UploadFile] = File(...),
    token: str = Depends(oauth2_scheme)
):
    try:
        # Validate input values
        if not name or not description or not price:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name, price, and description are required.")
        if quantity < 1 or price < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity or Price must be at least 1.")
        if not files or len(files) < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one image file is required.")

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
            "_id": str(ObjectId()),
            "seller_id": seller_id,
            "name": name,
            "description": description,
            "price": price,
            "quantity": quantity,
            "images": image_urls,
            "created_at": datetime.utcnow(),
            "isDeleted": False,
            "deleted_at": None
        }

        await db["products"].insert_one(product_dict)

        product_response = {
            "id": str(product_dict["_id"]),
            "seller_id": product_dict["seller_id"],
            "name": product_dict["name"],
            "description": product_dict["description"],
            "price": product_dict["price"],
            "quantity": product_dict["quantity"],
            "isAvailable": product_dict["quantity"] > 0,
            "images": [f"{config.PRODUCT_UPLOAD_PATH}/{img}" for img in product_dict["images"]],
            "created_at": product_dict["created_at"].isoformat()
        }

        await log_action("create_product", f"Product created by seller {seller_id}", True)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Product Created Successfully!", "product": product_response})

    except HTTPException as http_err:
        await log_action("create_product", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("create_product", str(e), False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")

@router.put("/update/{product_id}")
async def update_product(
    product_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    quantity: Optional[int] = Form(None),
    files: List[UploadFile] = File(None),
    token: str = Depends(oauth2_scheme)
):
    try:
        async with await db.client.start_session() as s:
            async with s.start_transaction():
                try:
                    seller_id = await SellerAuth(token)
                    
                    product = await db["products"].find_one({"_id": product_id, "isDeleted": False}, session=s)
                    if not product:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product Not Found.")
                    if product["seller_id"] != seller_id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this product.")

                    update_data = {}
                    if name:
                        update_data["name"] = name
                    if description:
                        update_data["description"] = description
                    if price is not None:
                        update_data["price"] = price
                    if quantity is not None:
                        update_data["quantity"] = quantity

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

                    updated_product = await db["products"].find_one_and_update(
                        {"_id": product_id},
                        {"$set": update_data},
                        return_document=True,
                        session=s
                    )

                    if not updated_product:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not authorized to update this product or product not found")

                    await log_action("update_product", f"Product {product_id} updated by seller {seller_id}", True)
                    return {
                        "id": str(updated_product["_id"]),
                        "name": updated_product["name"],
                        "description": updated_product["description"],
                        "price": updated_product["price"],
                        "quantity": updated_product["quantity"],
                        "isAvailable": updated_product["quantity"] > 0,
                        "images": [f"{config.PRODUCT_UPLOAD_PATH}/{img}" for img in updated_product["images"]],
                        "created_at": updated_product["created_at"]
                    }

                except HTTPException as http_err:
                    await log_action("update_product", http_err.detail, False)
                    raise http_err
                except Exception as e:
                    await log_action("update_product", str(e), False)
                    await s.abort_transaction()
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")
    except HTTPException as http_err:
        await log_action("update_product", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("update_product", str(e), False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")

@router.get("/GetAll")
async def get_all_products(
    search: Optional[str] = Query(None, description="Search term for name, description, or seller email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, gt=0, le=100, description="Number of products to return per page"),
    sort_by_price: Optional[bool] = Query(None, description="Sort by price if True")
):
    try:
        match_stage = {"isDeleted": False}
        if search:
            seller_ids = [user["_id"] for user in await db["users"].find({"email": {"$regex": search, "$options": "i"}}).to_list(length=None)]
            match_stage = {
                "$or": [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}},
                    {"seller_id": {"$in": seller_ids}}
                ],
                "isDeleted": False
            }

        sort_stage = {"price": 1} if sort_by_price else None
        skip = (page - 1) * limit

        pipeline = [
            {"$match": match_stage},
            {"$lookup": {
                "from": "users",
                "localField": "seller_id",
                "foreignField": "_id",
                "as": "seller"
            }},
            {"$unwind": "$seller"},
            {"$project": {
                "id": "$_id",
                "seller_email": "$seller.email",
                "name": 1,
                "description": 1,
                "price": 1,
                "quantity": 1,
                "isAvailable": {"$cond": {"if": {"$gt": ["$quantity", 0]}, "then": True, "else": False}},
                "images": 1,
                "created_at": 1
            }},
            {"$skip": skip},
            {"$limit": limit}
        ]

        if sort_stage:
            pipeline.insert(1, {"$sort": sort_stage})

        products = await db["products"].aggregate(pipeline).to_list(length=None)

        if not products:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found")

        for product in products:
            product["images"] = [f"{config.PRODUCT_UPLOAD_PATH}/{img}" for img in product["images"]]
            product["id"] = str(product["id"])

        await log_action("get_all_products", "All products retrieved", True)
        return products

    except HTTPException as http_err:
        await log_action("get_all_products", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("get_all_products", str(e), False)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "An error occurred while fetching products.", "error": str(e)})

@router.get("/getmineproducts")
async def get_mine_products(
    token: str = Depends(oauth2_scheme)
):
    try:
        seller_id = await SellerAuth(token)
        
        query = {"seller_id": seller_id, "isDeleted": False}

        products = await db["products"].find(query).to_list(length=None)
        if not products:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You haven't added any products yet!")

        product_responses = []
        for product in products:
            product_response = {
                "id": str(product["_id"]),
                "name": product["name"],
                "description": product["description"],
                "price": product["price"],
                "quantity": product["quantity"],
                "isAvailable": product["quantity"] > 0,
                "images": [f"{config.PRODUCT_UPLOAD_PATH}/{img}" for img in product["images"]],
                "created_at": product["created_at"]
            }
            product_responses.append(product_response)

        await log_action("get_mine_products", f"Products retrieved for seller {seller_id}", True)
        return product_responses

    except HTTPException as http_err:
        await log_action("get_mine_products", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("get_mine_products", str(e), False)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "An error occurred while fetching products.", "error": str(e)})

@router.get("/GetProduct/{product_id}")
async def get_product(product_id: str):
    try:
        pipeline = [
            {"$match": {"_id": ObjectId(product_id), "isDeleted": False}},  # Match the product by ID and isDeleted flag
            {
                "$lookup": {
                    "from": "users",  # Join with the users collection
                    "localField": "seller_id",
                    "foreignField": "_id",
                    "as": "seller_details"
                }
            },
            {"$unwind": "$seller_details"},  # Unwind the array of seller details
            {
                "$project": {  # Project the required fields
                    "id": "$_id",
                    "seller_email": "$seller_details.email",
                    "name": 1,
                    "description": 1,
                    "price": 1,
                    "quantity": 1,
                    "isAvailable": {"$cond": {"if": {"$gt": ["$quantity", 0]}, "then": True, "else": False}},
                    "images": 1,
                    "created_at": 1
                }
            }
        ]

        product = await db["products"].aggregate(pipeline).to_list(length=1)

        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        product = product[0]
        product["images"] = [f"{config.PRODUCT_UPLOAD_PATH}/{img}" for img in product["images"]]

        await log_action("get_product", f"Product {product_id} retrieved", True)
        return product

    except HTTPException as http_err:
        await log_action("get_product", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("get_product", str(e), False)
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/delete/{product_id}")
async def delete_product(
    product_id: str,
    token: str = Depends(oauth2_scheme)
):
    try:
        async with await db.client.start_session() as s:
            async with s.start_transaction():
                try:
                    seller_id = await SellerAuth(token)
                    product = await db["products"].find_one({"_id": product_id, "seller_id": seller_id, "isDeleted": False}, session=s)
                    
                    if not product:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this product")

                    await db["products"].update_one(
                        {"_id": product_id},
                        {"$set": {"isDeleted": True, "deleted_at": datetime.utcnow()}},
                        session=s
                    )
                    await db["shopping_carts"].delete_many({"product_id": product_id}, session=s)

                    await log_action("delete_product", f"Product {product_id} deleted by seller {seller_id}", True)
                    return {"message": "Product moved to bin successfully. You can restore it within 30 days."}

                except HTTPException as http_err:
                    await log_action("delete_product", http_err.detail, False)
                    await s.abort_transaction()
                    raise http_err
                except Exception as e:
                    await log_action("delete_product", str(e), False)
                    await s.abort_transaction()
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")
    except HTTPException as http_err:
        await log_action("delete_product", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("delete_product", str(e), False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")

@router.get("/getDeleted")
async def get_deleted_products(
    token: str = Depends(oauth2_scheme)
):
    try:
        seller_id = await SellerAuth(token)
        
        query = {"seller_id": seller_id, "isDeleted": True}

        products = await db["products"].find(query).to_list(length=None)
        if not products:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You haven't deleted any products yet!")

        product_responses = []
        for product in products:
            product_response = {
                "id": str(product["_id"]),
                "name": product["name"],
                "description": product["description"],
                "price": product["price"],
                "quantity": product["quantity"],
                "isAvailable": product["quantity"] > 0,
                "images": [f"{config.PRODUCT_UPLOAD_PATH}/{img}" for img in product["images"]],
                "created_at": product["created_at"]
            }
            product_responses.append(product_response)

        await log_action("get_deleted_products", f"Deleted products retrieved for seller {seller_id}", True)
        return product_responses

    except HTTPException as http_err:
        await log_action("get_deleted_products", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("get_deleted_products", str(e), False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")

@router.put("/restore/{product_id}")
async def restore_product(
    product_id: str,
    token: str = Depends(oauth2_scheme)
):
    try:
        seller_id = await SellerAuth(token)
        product = await db["products"].find_one({"_id": product_id, "seller_id": seller_id, "isDeleted": True})
        if not product:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to restore this product")

        deleted_time = product["deleted_at"]
        if deleted_time and (datetime.utcnow() - deleted_time) > timedelta(days=30):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot restore the product. The 30-day restoration period has expired.")

        await db["products"].update_one({"_id": product_id}, {"$set": {"isDeleted": False, "deleted_at": None}})
        await log_action("restore_product", f"Product {product_id} restored by seller {seller_id}", True)
        return {"message": "Product restored successfully."}
    except HTTPException as http_err:
        await log_action("restore_product", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("restore_product", str(e), False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")

# Scheduler function to remove products that are deleted for more than 30 days( runs daily at the midnight)
def remove_old_deleted_products():
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        db["products"].delete_many({"isDeleted": True, "deleted_at": {"$lte": cutoff_date}})
        print("Scheduler: Removed products deleted more than 30 days ago")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")

# Initialize and start the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(remove_old_deleted_products, 'cron', hour=0, minute=0)
scheduler.start()
