from fastapi import APIRouter, Depends, HTTPException
from backend.auth.dependencies import get_current_user, require_pharmacist
from backend.database import db

router = APIRouter()

@router.get("")
async def list_medicines():
    meds = await db.medicines.find({}).to_list(100)
    for m in meds: m["_id"] = str(m["_id"])
    return meds

@router.patch("/{product_id}/stock")
async def update_stock(product_id: str, stock_level: int, user = Depends(require_pharmacist)):
    res = await db.medicines.update_one(
        {"product_id": product_id},
        {"$set": {"stock_level": stock_level}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return {"message": "Stock updated"}

@router.patch("/{product_id}/stock/add")
async def add_stock(product_id: str, amount: int, user = Depends(require_pharmacist)):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    res = await db.medicines.update_one(
        {"product_id": product_id},
        {"$inc": {"stock_level": amount}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return {"message": f"Added {amount} units to stock"}
