import csv
import io
from bson import ObjectId
from fastapi import Depends, APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, ValidationError
from models import BlacklistedToken, Log, User
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
    if not verify_password(password, user.hashed_password):
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

async def blacklist_token(token: str):
    blacklisted_token = BlacklistedToken(
        token=token,
        blacklisted_at=datetime.utcnow()
    )
    await db["blacklisted_tokens"].insert_one(blacklisted_token.dict(by_alias=True))

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
        user = await get_user_by_id(seller_id)
        if user.is_seller == False:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return seller_id

async def BuyerAuth(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db["users"].find_one({"_id": user_id})
    if user is None or user["is_seller"]:
        raise credentials_exception
    return user_id

async def UserAuth(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db["users"].find_one({"_id": user_id})
    if user is None:
        raise credentials_exception
    return user

async def log_action(action: str, message: str, success: bool):
    log = Log(action=action, message=message, success=success)
    await db["logs"].insert_one(log.dict(by_alias=True))


@router.get("/export-logs")
async def export_logs():
    try:
        logs_cursor = db["logs"].find()
        logs = await logs_cursor.to_list(length=None)
        
        if not logs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No logs found")

        # Prepare CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        headers = ["action", "message", "success", "timestamp"]
        writer.writerow(headers)

        # Write log rows
        for log in logs:
            writer.writerow([log.get("action"), 
                             log.get("message"),
                             log.get("success"),              
                             log.get("timestamp").strftime("%Y-%m-%d %H:%M:%S") if log.get("timestamp") else ""])

        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=logs.csv"})

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")

@router.post("/register")
async def register(request: Request):
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        is_seller = body.get("is_seller")
        
        if email is None or password is None or is_seller is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All fields are required"
            )

        existing_user = await db["users"].find_one({"email": email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        hashed_password = get_password_hash(password)
        user_dict = User(
            email=email,
            hashed_password=hashed_password,
            id=str(ObjectId()), 
            is_seller=is_seller,
            verified=False,
            created_at=datetime.utcnow()
        )

        # Create a verification token
        token_data = {
            "email": email,
            "exp": datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)  # token expires in 24 hours
        }
        token = jwt.encode(token_data, config.SECRET_KEY, algorithm=config.ALGORITHM)

        # Send verification email
        send_verification_email(email, token)

        await db["users"].insert_one(user_dict.dict(by_alias=True))

        user_type = "seller" if is_seller else "buyer"
        await log_action("register", f"User {email} registered as {user_type}", True)
        
        return {"message": f"Welcome {email}! We've sent a verification link, please check your mail."}

    except HTTPException as http_err:
        await log_action("register", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("register", str(e), False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


   
@router.post("/login")
async def login_for_access_token(request: Request):
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        user = await authenticate_user(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if  user.verified==False:
            # Create a verification token
            token_data = {
                "email": email,
                "exp": datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)  # token expires in 24 hours
            }
            token = jwt.encode(token_data, config.SECRET_KEY, algorithm=config.ALGORITHM)

            # Send verification email
            send_verification_email(email, token)
            await log_action("login", f"User {email} was sent an email to verify his identity", True)
            return {"message": f"Welcome Back! We've sent a verification link, please check your mail."}
            
        access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await create_access_token(
            data={"sub": user.id, "isSeller": user.is_seller}, expires_delta=access_token_expires
        )
        await log_action("login", f"User {email} logged in", True)
        return {"access_token": access_token, "message": "Welcome Back!"}
    except HTTPException as http_err:
        await log_action("login", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("login", str(e), False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")


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
        await log_action("verify_email", f"User {email} verified email", True)
        return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)
    except HTTPException as http_err:
        await log_action("verify_email", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("verify_email", str(e), False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")
    
 

@router.post("/forgot-password")
async def forgot_password(request: Request):
    try:
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

        await log_action("forgot_password", f"Password reset link sent to {email}", True)
        return {"message": "Password reset link sent to your email"}
    except HTTPException as http_err:
        await log_action("forgot_password", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("forgot_password", str(e), False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")

@router.get("/reset-password")
async def reset_password_page(token: str):
    try:
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
        await log_action("reset_password_page", "Password reset page accessed", True)
        return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)
    except HTTPException as http_err:
        await log_action("reset_password_page", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("reset_password_page", str(e), False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")

@router.post("/reset-password")
async def reset_password(request: Request):
    try:
        body = await request.form()
        token = body.get("token")
        new_password = body.get("new_password")

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
        await log_action("reset_password", f"Password reset for {email}", True)
        return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)
    except HTTPException as http_err:
        await log_action("reset_password", http_err.detail, False)
        raise http_err
    except Exception as e:
        await log_action("reset_password", str(e), False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something Went Wrong!")
