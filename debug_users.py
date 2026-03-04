import asyncio
from backend.routers.users import get_patients
from backend.database import connect_to_mongo

async def main():
    await connect_to_mongo()
    mock_pharmacist = {"role": "pharmacist", "patient_id": "PH000"}
    try:
        res = await get_patients(mock_pharmacist)
        print("Success:", len(res))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
