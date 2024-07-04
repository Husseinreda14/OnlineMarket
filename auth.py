from bson import ObjectId
from fastapi import Depends, APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from models import User, Token
from db import db
import config
from sideFunctions import send_reset_password_email, send_verification_email

SECRET_KEY = config.SECRET_KEY
ALGORITHM = config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user_by_email(email: str):
    user = await db["users"].find_one({"email": email})
    if user:
        return User(**user)
async def get_user_by_id(id: str):
    user = await db["users"].find_one({"_id": id})
    if user:
        return User(**user)
async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password) or user.verified==False:
        return False
    return user


async def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    while True:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        if not await is_token_blacklisted(encoded_jwt):
            return encoded_jwt

def get_password_hash(password):
    return pwd_context.hash(password)


    
async def blacklist_token(token: str):
    blacklisted_token = {
        "token": token,
        "blacklisted_at": datetime.utcnow()
    }
    await db["blacklisted_tokens"].insert_one(blacklisted_token)

async def is_token_blacklisted(token: str) -> bool:
    token_doc = await db["blacklisted_tokens"].find_one({"token": token})
    return token_doc is not None


async def SellerAuth(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if await is_token_blacklisted(token):
            raise credentials_exception
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        seller_id: str = payload.get("sub")
        if seller_id is None:
            raise credentials_exception
        user=await get_user_by_id(seller_id)
        if user.is_seller==False:
            raise credentials_exception
        
        

    except JWTError:
        raise credentials_exception
    return seller_id



@router.post("/registerAsSeller")
async def register(request: Request):
    body = await request.json()
    email = body.get("email")
    password = body.get("password")
    
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    existing_user = await db["users"].find_one({"email": email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(password)
    user_dict = {
        "email": email,
        "hashed_password": hashed_password,
        "_id": str(ObjectId()),
        "is_seller" : True,
        "verified": False,  # Add verified attribute
        "created_at": datetime.utcnow()
    }

    # Create a verification token
    token_data = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)  # token expires in 24 hours
    }
    token = jwt.encode(token_data, config.SECRET_KEY, algorithm=config.ALGORITHM)

    # Send verification email
    send_verification_email(email, token)

    await db["users"].insert_one(user_dict)
    
    return {"message": f"Welcome {email}! We've sent a verification link check you mail."}

@router.post("/registerAsBuyer")
async def register(request: Request):
    body = await request.json()
    email = body.get("email")
    password = body.get("password")
    
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    existing_user = await db["users"].find_one({"email": email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(password)
    user_dict = {
        "email": email,
        "hashed_password": hashed_password,
        "_id": str(ObjectId()),
        "is_seller" : False,
        "verified": False,  # Add verified attribute
        "created_at": datetime.utcnow()
    }

    # Create a verification token
    token_data = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)  # token expires in 24 hours
    }
    token = jwt.encode(token_data, config.SECRET_KEY, algorithm=config.ALGORITHM)

    # Send verification email
    send_verification_email(email, token)

    await db["users"].insert_one(user_dict)
    
    return {"message": f"Welcome {email}! We've sent a verification link check you mail."}

@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email(token: str):
    try:
        if await is_token_blacklisted(token):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")


        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email = payload.get("email")
        if email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        
        await db["users"].update_one({"email": email}, {"$set": {"verified": True}})
        await blacklist_token(token)
        
        html_content = """
        <html>
            <head>
                <title>Email Verified</title>
            </head>
            <body>
                <h1>Email Verified Successfully!</h1>
                <p>You can now login to your account!</p>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")


@router.post("/login")
async def login_for_access_token(request: Request):
    body = await request.json()
    email = body.get("email")
    password = body.get("password")
    user = await authenticate_user(email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password, or email not verified",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.id, "isSeller": user.is_seller}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
@router.post("/forgot-password")
async def forgot_password(request: Request):
    body = await request.json()
    email = body.get("email")
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )

    # Create a password reset token
    token_data = {
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(minutes=15)  # token expires in 15 minutes
    }
    token = jwt.encode(token_data, config.SECRET_KEY, algorithm=config.ALGORITHM)

    # Send password reset email
    reset_url = f"{config.API_URL}/reset-password?token={token}"
    send_reset_password_email(user.email, token)

    return {"message": "Password reset link sent to your email"}

@router.get("/reset-password")
async def reset_password_page(token: str):
    if await is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    html_content = f"""
    <html>
        <head>
            <title>Reset Password</title>
        </head>
        <body>
            <h1>Reset Your Password</h1>
            <form action="/auth/reset-password" method="post">
                <input type="hidden" name="token" value="{token}">
                <label for="new_password">New Password:</label><br>
                <input type="password" id="new_password" name="new_password"><br><br>
                <input type="submit" value="Reset Password">
            </form>
        </body>
    </html>
    """
    await blacklist_token(token)
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)


@router.post("/reset-password")
async def reset_password(request: Request):
    body = await request.form()
    token = body.get("token")
    new_password = body.get("new_password")

    try:



        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email = payload.get("email")
        if email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        
        new_hashed_password = get_password_hash(new_password)
        await db["users"].update_one({"email": email}, {"$set": {"hashed_password": new_hashed_password}})

        
        html_content = """
        <html>
            <head>
                <title>Password Reset Successful</title>
            </head>
            <body>
                <h1>Password Reset Successful</h1>
                <p>Your password has been reset successfully. You can now login with your new password.</p>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")