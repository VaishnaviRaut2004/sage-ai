from langchain_core.tools import tool
from backend.database import db
from datetime import datetime, timedelta

@tool
async def get_low_stock_report(threshold: int = 20) -> str:
    """Gets a report of all medicines currently low on stock based on a threshold. Default threshold is 20."""
    try:
        cursor = db.medicines.find({"stock_level": {"$lt": threshold}})
        items = await cursor.to_list(length=100)
        
        if not items:
            return "No medicines are currently running low on stock."
            
        report = f"Low Stock Report (Threshold: {threshold}):\n"
        for item in items:
            report += f"- {item.get('name', 'Unknown')}: {item.get('stock_level', 0)} units remaining\n"
            
        return report
    except Exception as e:
        return f"Error retrieving low stock report: {str(e)}"

@tool
async def get_refill_alerts() -> str:
    """Checks for upcoming or active medication refill alerts across all patients."""
    try:
        now = datetime.utcnow()
        cursor = db.refill_predictions.find({"next_refill_date": {"$gte": now - timedelta(days=7), "$lt": now + timedelta(days=7)}})
        alerts = await cursor.to_list(length=100)
        
        if not alerts:
            return "No active refill alerts for the upcoming week."
            
        report = "Upcoming/Recent Refill Alerts:\n"
        for alert in alerts:
            med_name = alert.get("medicine", "Unknown Medicine")
            pat_id = alert.get("patient_id", "Unknown Patient")
            refill_date = alert.get("next_refill_date")
            date_str = refill_date.strftime("%Y-%m-%d") if refill_date else "Unknown Date"
            report += f"- Patient {pat_id} needs {med_name} by {date_str}\n"
            
        return report
    except Exception as e:
        return f"Error retrieving refill alerts: {str(e)}"

@tool
async def restock_medicine(medicine_name: str, quantity: int) -> str:
    """Restocks a specific medicine by adding the given quantity to its inventory."""
    if quantity <= 0:
        return "Quantity must be greater than zero."
        
    try:
        # Exact/case-insensitive search to prevent partial match collisions
        med = await db.medicines.find_one({"name": {"$regex": f"^{medicine_name}$", "$options": "i"}})
        if not med:
            return f"Error: Medicine '{medicine_name}' not found in inventory."
            
        result = await db.medicines.update_one(
            {"_id": med["_id"]},
            {"$inc": {"stock_level": quantity}}
        )
        
        if result.modified_count == 1:
            new_stock = med.get('stock_level', 0) + quantity
            return f"Successfully restocked '{med['name']}' with {quantity} units. New abstract balance is {new_stock} units."
        else:
            return "Failed to update stock. Please try again."
    except Exception as e:
        return f"Error restocking medicine: {str(e)}"

@tool
async def get_order_history(patient_id: str = None) -> str:
    """Retrieves recent orders from the system. If patient_id is provided, filters for that specific patient."""
    try:
        query = {}
        if patient_id and patient_id.strip():
            query = {"patient_id": {"$regex": f"{patient_id}", "$options": "i"}}
            
        cursor = db.orders.find(query).sort("created_at", -1).limit(10)
        orders = await cursor.to_list(length=10)
        
        if not orders:
            if patient_id:
                return f"No recent orders found for patient {patient_id}."
            return "No recent orders found in the system."
            
        report = "Recent Order History:\n"
        for o in orders:
            items_str = ", ".join([f"{item.get('quantity', 0)}x {item.get('medicine_name', 'Unknown')}" for item in o.get('items', [])])
            status = o.get("status", "Unknown")
            pid = o.get("patient_id", "Unknown")
            order_id = str(o.get("_id", "Unknown"))[-6:] # Shorthand id
            report += f"- [{order_id}] {pid} ordered: {items_str} ({status})\n"
            
        return report
    except Exception as e:
        return f"Error retrieving order history: {str(e)}"
