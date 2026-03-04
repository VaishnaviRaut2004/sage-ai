from fastapi import APIRouter, Depends
from backend.auth.dependencies import require_pharmacist
from backend.database import db

router = APIRouter()

@router.get("")
async def get_patients(user = Depends(require_pharmacist)):
    patients = await db.users.find({"role": "patient"}, {"password_hash": 0}).to_list(100)
    for p in patients:
        p["_id"] = str(p["_id"])
        
        # Convert ObjectIds in purchase_history to strings if present
        if "purchase_history" in p and isinstance(p["purchase_history"], list):
            p["purchase_history"] = [str(hid) for hid in p["purchase_history"]]
            
        # Hydrate order count and total spend
        orders = await db.orders.find({"patient_id": p["patient_id"]}).to_list(None)
        p["total_orders"] = len(orders)
        p["total_spend"] = sum(float(o.get("total_price", 0) or 0) for o in orders)
        
    return patients
