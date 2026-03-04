from backend.graph_state import AgentState
from backend.database import db
from datetime import datetime, timedelta
import uuid

# Re-usable logic for cron job and agent
dosage_frequency_map = {
    "Once daily": 1, 
    "Twice daily": 2, 
    "Three times daily": 3, 
    "Weekly": 1/7, 
    "As needed": 0.5
}

def calculate_expected_runout(purchase_date: datetime, units_per_pack: int, dosage_frequency: str) -> datetime:
    daily_consumption = dosage_frequency_map.get(dosage_frequency, 1)
    if daily_consumption == 0: 
        daily_consumption = 1
        
    days_supply = units_per_pack / daily_consumption
    return purchase_date + timedelta(days=days_supply)
    
async def run_prediction_check(patient_id: str):
    # This runs prediction on a single user for on-demand checking
    user = await db.users.find_one({"patient_id": patient_id})
    if not user: return False
    
    alerts_created = 0
    now = datetime.now()
    
    # We really only care about latest orders, but let's scan recent ones
    recent_orders = await db.orders.find({"patient_id": patient_id}).sort("purchase_date", -1).to_list(10)
    
    for order in recent_orders:
        freq = order.get("dosage_frequency", "Once daily")
        med = await db.medicines.find_one({"product_id": order["product_id"]})
        if not med: continue
        
        units = med.get("units_per_pack", 30)
        runout_date = calculate_expected_runout(order["purchase_date"], units, freq)
        
        # Is within 7 days or already run out recently?
        days_remaining = (runout_date - now).days
        
        if 0 <= days_remaining <= 7:
            # Create alert if not exists
            existing = await db.refill_alerts.find_one({
                "patient_id": patient_id, 
                "medicine_name": med["name"], 
                "notified": False
            })
            
            if not existing:
                alert_doc = {
                    "alert_id": f"ALT-{uuid.uuid4().hex[:8]}",
                    "patient_id": patient_id,
                    "patient_name": user["name"],
                    "medicine_name": med["name"],
                    "expected_runout_date": runout_date,
                    "days_remaining": days_remaining,
                    "last_purchase_date": order["purchase_date"],
                    "notified": False,
                    "created_at": now
                }
                from backend.services.email_service import send_refill_alert_email
                await db.refill_alerts.insert_one(alert_doc)
                alerts_created += 1
                
                # Send email to patient
                patient_email = user.get("email")
                if patient_email:
                    await send_refill_alert_email(patient_email, alert_doc)
                
    return alerts_created > 0

async def prediction_agent_node(state: AgentState):
    # Run the prediction for this patient in the background
    pat_id = state.get("patient_id")
    if pat_id:
        has_alert = await run_prediction_check(pat_id)
        # We could add info to the agent state, but prompt only requires it update the DB
    return state
