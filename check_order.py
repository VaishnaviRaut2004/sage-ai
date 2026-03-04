import asyncio
import motor.motor_asyncio

async def check_order():
    client = motor.motor_asyncio.AsyncIOMotorClient('mongodb+srv://admin:admin123@cluster0.n1q16.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    db = client['dhanvan_ai']
    order = await db.orders.find_one({'order_id': 'ORD-20260301125005-D0FA'})
    print(f"ORDER_FOUND: {order is not None}")
    if order:
        print(order)

if __name__ == "__main__":
    asyncio.run(check_order())
