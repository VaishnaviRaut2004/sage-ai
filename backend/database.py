from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

class Database:
    client: AsyncIOMotorClient = None
    db = None

    def __getattr__(self, name):
        if self.db is None:
            raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
        return getattr(self.db, name)

db = Database()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(MONGO_URI)
    db.db = db.client.dhanvan
    print("Connected to MongoDB")

async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")
