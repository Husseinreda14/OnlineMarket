from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

def to_object_id(value: str) -> ObjectId:
    return ObjectId(value)

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    email: EmailStr
    hashed_password: str
    is_seller: bool = False
    verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    seller_id: str = Field(..., description="The ID of the seller")
    name: str
    description: str
    quantity: int
    price: float
    images: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    isDeleted: bool = False
    deleted_at: Optional[datetime] = None

class ShoppingCart(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str = Field(..., description="The ID of the user")
    product_id: str = Field(..., description="The ID of the product")
    quantity: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    seller_id: str = Field(..., description="The ID of the seller")
    user_id: str = Field(..., description="The ID of the user")
    payment_id: str
    products: List[ShoppingCart]
    total_price: float
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str = Field(..., description="The ID of the user")
    payment_id: str
    payment_method: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BlacklistedToken(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    token: str
    blacklisted_at: datetime = Field(default_factory=datetime.utcnow)


class Log(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    action: str
    message: str
    success: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)