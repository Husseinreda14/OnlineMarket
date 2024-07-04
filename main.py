from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from db import connect_to_mongo, close_mongo_connection
from routes import router as main_route

app = FastAPI()

app.include_router(main_route)
# Serve static files from the 'uploads' directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()
