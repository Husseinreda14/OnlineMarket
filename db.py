# db.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import config
uri = config.DATABASE_URI

# Initialize the MongoDB client
client = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
db = client.get_default_database()

async def ping_server():
    # Send a ping to confirm a successful connection
    try:
        await client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

async def connect_to_mongo():
    await ping_server()

async def close_mongo_connection():
    client.close()
    print("MongoDB connection closed")
