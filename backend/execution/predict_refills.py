import asyncio
from datetime import datetime
import uuid
from backend.database import db
from backend.agents.prediction_agent import calculate_expected_runout

async def run_all_predictions():
    print("Starting hourly prediction job...")
    now = datetime.now()
    alerts_created = 0
    
    # Get all patients
    patients = await db.users.find({"role": "patient"}).to_list(1000)
    
    for pat in patients:
        pat_id = pat["patient_id"]
        # Only check recent orders to not spam for 5 year old orders
        # Find the latest order per medicine
        pipeline = [
            {"$match": {"patient_id": pat_id}},
            {"$sort": {"purchase_date": -1}},
            {"$group": {
                "_id": "$product_id",
                "latest_order": {"$first": "$$ROOT"}
            }}
        ]
        
        latest_orders = await db.orders.aggregate(pipeline).to_list(None)
        
        for g in latest_orders:
            order = g["latest_order"]
            freq = order.get("dosage_frequency", "Once daily")
            med_name = order.get("medicine_name")
            
            med = await db.medicines.find_one({"product_id": order["product_id"]})
            if not med: continue
            
            units = med.get("units_per_pack", 30)
            if units <= 0: units = 30 # fallback
            
            runout_date = calculate_expected_runout(order["purchase_date"], units, freq)
            days_remaining = (runout_date - now).days
            
            if 0 <= days_remaining <= 7:
                # Check for existing pending alert
                existing = await db.refill_alerts.find_one({
                    "patient_id": pat_id, 
                    "medicine_name": med_name, 
                    "notified": False
                })
                
                if not existing:
                    alert_doc = {
                        "alert_id": f"ALT-{uuid.uuid4().hex[:8]}",
                        "patient_id": pat_id,
                        "patient_name": pat["name"],
                        "medicine_name": med_name,
                        "expected_runout_date": runout_date,
                        "days_remaining": days_remaining,
                        "last_purchase_date": order["purchase_date"],
                        "notified": False,
                        "created_at": now
                    }
                    from backend.services.email_service import send_refill_alert_email
                    await db.refill_alerts.insert_one(alert_doc)
                    alerts_created += 1
                    
                    patient_email = pat.get("email")
                    if patient_email:
                        await send_refill_alert_email(patient_email, alert_doc)

    print(f"Prediction job complete. {alerts_created} new alerts created.")

if __name__ == "__main__":
    from backend.database import connect_to_mongo
    async def test():
        await connect_to_mongo()
        await run_all_predictions()
    asyncio.run(test())
