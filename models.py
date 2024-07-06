from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pydantic.json import pydantic_encoder

def to_object_id(value: str) -> ObjectId:
    return ObjectId(value)


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    email: EmailStr
    hashed_password: str
    is_seller: bool = False
    verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "id": "60dbf46dcf1e9d96f6e40876",
                "email": "user@example.com",
                "hashed_password": "hashedpassword",
                "is_active": True,
                "is_seller": False,
                "verified": False,
                "created_at": "2021-06-30T00:00:00Z",
            }
        }

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    seller_id: str
    name: str
    description: str
    quantity: int
    price: float
    images: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    isDeleted: bool = False
    deleted_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "id": "60dbf46dcf1e9d96f6e40876",
                "seller_id": "60dbf46dcf1e9d96f6e40876",
                "seller_email": "seller@example.com",
                "name": "Product Name",
                "description": "Product Description",
                "price": 99.99,
                "quantity": 10,
                "images": ["/uploads/productimages/image1.jpg", "/uploads/productimages/image2.jpg"],
                "created_at": "2021-06-30T00:00:00Z",
                "isDeleted": False,
                "deleted_at": None,            }
        }
class ShoppingCart(BaseModel):
    id:str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str = Field(..., description="The ID of the user")
    product_id: str = Field(..., description="The ID of the product")
    quantity: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "user_id": "60dbf46dcf1e9d96f6e40876",
                "product_id": "60dbf46dcf1e9d96f6e40876",
                "quantity": 2,
                "created_at": "2021-06-30T00:00:00Z",
                "updated_at": "2021-06-30T00:00:00Z",
            }
        }
class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    seller_id:str
    user_id: str
    payment_id:str
    products: List[ShoppingCart]
    total_price: float
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "id": "60dbf46dcf1e9d96f6e40876",
                "seller_id":"60dbf46dcf1e9d96f6e40876",
                "user_id": "60dbf46dcf1e9d96f6e40876",
                "payment_id": "60dbf46dcf1e9d96f6e40876",
                "products": [{"product_id": "60dbf46dcf1e9d96f6e40876", "quantity": 2}],
                "total_price": 199.98,
                "status": "pending",
                "created_at": "2021-06-30T00:00:00Z",
                "updated_at": "2021-06-30T00:00:00Z",
            }
        }

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    payment_id: str
    payment_method:str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "id": "60dbf46dcf1e9d96f6e40876",
                "user_id": "60dbf46dcf1e9d96f6e40876",
                "payment_id": "pi_1IeYQ2LM7NV5XtZzlw8Tx6KJ",
                "order_id": "60dbf46dcf1e9d96f6e40876",
                "status": "pending",
                "created_at": "2021-06-30T00:00:00Z",
                "updated_at": "2021-06-30T00:00:00Z",
            }
        }


class Token(BaseModel):
    access_token: str
    token_type: str


class BlacklistedToken(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    token: str
    blacklisted_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "id": "60dbf46dcf1e9d96f6e40876",
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "blacklisted_at": "2021-06-30T00:00:00Z",
            }
        }
