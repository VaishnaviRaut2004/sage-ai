from fastapi import APIRouter, Depends, HTTPException
from backend.auth.dependencies import get_current_user, require_pharmacist
from backend.database import db
from backend.execution.predict_refills import run_all_predictions

router = APIRouter()

@router.get("/alerts")
async def get_alerts(user = Depends(get_current_user)):
    if user["role"] == "pharmacist":
        alerts = await db.refill_alerts.find({}).sort("expected_runout_date", 1).to_list(100)
    else:
        alerts = await db.refill_alerts.find({"patient_id": user["patient_id"]}).sort("expected_runout_date", 1).to_list(100)
        
    # Convert ObjectIds to str
    for a in alerts:
        a["_id"] = str(a["_id"])
    return alerts

@router.post("/run")
async def trigger_run(user = Depends(require_pharmacist)):
    # Manual trigger for demo
    await run_all_predictions()
    return {"message": "Prediction job completed"}

from bson.objectid import ObjectId
from backend.services.email_service import send_refill_alert_email

@router.post("/alerts/{alert_id}/notify")
async def notify_alert(alert_id: str, user = Depends(require_pharmacist)):
    alert = await db.refill_alerts.find_one({"_id": ObjectId(alert_id)})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    pat = await db.users.find_one({"patient_id": alert["patient_id"]})
    if pat and pat.get("email"):
        await send_refill_alert_email(pat["email"], alert)

    result = await db.refill_alerts.update_one(
        {"_id": ObjectId(alert_id)},
        {"$set": {"notified": True}}
    )
    return {"message": "Alert marked as notified and email sent"}
