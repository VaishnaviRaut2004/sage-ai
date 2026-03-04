from backend.graph_state import AgentState
from backend.database import db
from backend.services.webhook_service import fire_fulfillment_webhook, fire_procurement_webhook
from backend.services.pdf_service import generate_invoice_pdf
from backend.services.email_service import send_order_confirmation
from datetime import datetime

async def action_agent_node(state: AgentState):
    if not state.get("validation_passed") or not state.get("stock_sufficient"):
        return state
        
    if state.get("intent_type") != "ordering":
        return state

    entities = state.get("extracted_entities", {})
    pat_id = state.get("patient_id")
    qty = entities.get("quantity", 1)
    
    user = await db.users.find_one({"patient_id": pat_id})
    if not user:
        state["agent_reply"] = "Error: Patient record not found."
        return state
        
    med = await db.medicines.find_one({"product_id": entities["product_id"]})
    
    # Decrement Stock
    await db.medicines.update_one(
        {"product_id": entities["product_id"]},
        {"$inc": {"stock_level": -qty}}
    )
    
    # Create Order
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    total_price = float(entities["unit_price"]) * qty
    
    order_doc = {
        "order_id": order_id,
        "patient_id": pat_id,
        "patient_name": user["name"],
        "medicine_name": entities["medicine"],
        "product_id": entities["product_id"],
        "pzn": entities["pzn"],
        "quantity": qty,
        "unit_price": float(entities["unit_price"]),
        "total_price": total_price,
        "dosage_frequency": entities.get("dosage_frequency", "As directed"),
        "purchase_date": datetime.now(),
        "prescription_required": state.get("prescription_required", False),
        "prescription_image_url": None,
        "status": "pending",
        "delivery_address": {
            "street": "Shivaji Chawk",
            "city": "Latur",
            "postal_code": "413512",
            "country": "India"
        },
        "payment_info": {
            "method": "card",
            "status": "pending",
            "transaction_id": None
        },
        "invoice_id": order_id,
        "approved_by_pharmacist": None,
        "webhook_triggered": True,
        "langsmith_trace_id": state.get("langsmith_trace_id"),
        "langsmith_trace_url": state.get("langsmith_trace_url"),
        "created_at": datetime.now()
    }
    
    res = await db.orders.insert_one(order_doc)
    await db.users.update_one(
        {"patient_id": pat_id},
        {"$push": {"purchase_history": res.inserted_id}}
    )
    
    # Generate Invoice
    invoice_path = await generate_invoice_pdf(order_doc, "Dhanvan AI Pipeline", "AI-001")
    
    # Email Order Confirmation
    patient_email = user.get("email")
    if patient_email:
        await send_order_confirmation(patient_email, order_doc, invoice_path)
    
    # Fire Webhooks
    await fire_fulfillment_webhook(order_doc)
    
    if state.get("reorder_triggered", False):
        await fire_procurement_webhook(
            medicine_name=entities["medicine"],
            pzn=entities["pzn"],
            current_stock=med["stock_level"] - qty,
            threshold=med["reorder_threshold"]
        )
        
    state["order_id"] = order_id
    state["agent_reply"] = f"Your order for {qty}x {entities['medicine']} has been successfully placed! Order ID: {order_id}. Total: ₹{total_price:.2f}."
    
    return state
