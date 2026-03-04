from fastapi import APIRouter, Depends, HTTPException
from backend.auth.dependencies import get_current_user, require_pharmacist
from backend.database import db
from bson import ObjectId

router = APIRouter()

@router.get("")
async def get_orders(user = Depends(get_current_user)):
    if user["role"] == "pharmacist":
        orders = await db.orders.find({}).sort("created_at", -1).to_list(100)
    else:
        orders = await db.orders.find({"patient_id": user["patient_id"]}).sort("created_at", -1).to_list(100)
    
    for o in orders:
        o["_id"] = str(o["_id"])
    return orders

@router.post("/{order_id}/pay")
async def pay_order(order_id: str, user = Depends(get_current_user)):
    print(f"[DEBUG] pay_order called for order_id: '{order_id}'")
    order = await db.orders.find_one({"order_id": order_id})
    if not order:
        print(f"[DEBUG] Order not found in DB for order_id: '{order_id}'")
        # Try finding by _id just in case
        try:
            from bson import ObjectId
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
            if order:
                print(f"[DEBUG] Found order by ObjectId instead: '{order_id}'")
        except:
            pass
            
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
        
    if user["role"] == "patient" and order["patient_id"] != user["patient_id"]:
        print(f"[DEBUG] UI unauthorized: user={user['patient_id']}, order={order['patient_id']}")
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    res = await db.orders.update_one(
        {"order_id": order["order_id"]}, 
        {"$set": {"status": "payment completed"}}
    )
    if res.matched_count == 0:
         raise HTTPException(status_code=404, detail="Order not found during update")
         
    return {"message": "Payment successful"}

@router.get("/{id}")
async def get_order(id: str, user = Depends(get_current_user)):
    order = await db.orders.find_one({"order_id": id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if user["role"] == "patient" and order["patient_id"] != user["patient_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    order["_id"] = str(order["_id"])
    return order

@router.patch("/{id}/status")
async def update_status(id: str, status: str, user = Depends(require_pharmacist)):
    # Simple validation
    if status not in ["pending", "approved", "fulfilled", "rejected", "payment completed"]:
         raise HTTPException(status_code=400, detail="Invalid status")
         
    res = await db.orders.update_one(
        {"order_id": id}, 
        {"$set": {"status": status, "approved_by_pharmacist": user["staff_id"]}}
    )
    if res.matched_count == 0:
         raise HTTPException(status_code=404, detail="Order not found")
         
    return {"message": "Order status updated"}
