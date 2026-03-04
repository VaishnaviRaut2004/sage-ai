import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check():
    uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(uri)
    
    # Check "dhanvan" database
    db_dhanvan = client.dhanvan
    order_dhanvan = await db_dhanvan.orders.find_one({"order_id": "ORD-20260301125005-D0FA"})
    print(f"DHANVAN_ORDER: {order_dhanvan is not None}")
    
    # Check "pharmacy_agent_db" database
    db_pharma = client.pharmacy_agent_db
    order_pharma = await db_pharma.orders.find_one({"order_id": "ORD-20260301125005-D0FA"})
    print(f"PHARMA_ORDER: {order_pharma is not None}")
    
    # List all databases
    dbs = await client.list_database_names()
    print(f"DATABASES: {dbs}")

if __name__ == "__main__":
    asyncio.run(check())
