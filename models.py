from pydantic import BaseModel, Field, EmailStr
from typing import List
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
    quantity:int
    price: float
    images: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "id": "60dbf46dcf1e9d96f6e40876",
                "seller_id": "60dbf46dcf1e9d96f6e40876",
                "seller_name": "seller@example.com",
                "name": "Product Name",
                "description": "Product Description",
                "price": 99.99,
                "images": ["/uploads/productimages/image1.jpg", "/uploads/productimages/image2.jpg"],
                "created_at": "2021-06-30T00:00:00Z",
            }
        }



class CartItem(BaseModel):
    product_id: str
    quantity: int

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "product_id": "60dbf46dcf1e9d96f6e40876",
                "quantity": 2,
            }
        }

class ShoppingCart(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    items: List[CartItem] = []
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
                "items": [{"product_id": "60dbf46dcf1e9d96f6e40876", "quantity": 2}],
                "created_at": "2021-06-30T00:00:00Z",
                "updated_at": "2021-06-30T00:00:00Z",
            }
        }

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    products: List[CartItem]
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
                "user_id": "60dbf46dcf1e9d96f6e40876",
                "products": [{"product_id": "60dbf46dcf1e9d96f6e40876", "quantity": 2}],
                "total_price": 199.98,
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
