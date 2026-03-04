from backend.graph_state import AgentState
from backend.database import db

async def pharmacy_agent_node(state: AgentState):
    # This acts as the policy layer.
    intent = state.get("intent_type")
    
    # We only need to validate if intent is ordering
    if intent != "ordering":
        state["validation_passed"] = True
        return state
        
    entities = state.get("extracted_entities", {})
    medicine_name = entities.get("medicine")
    
    if not medicine_name:
        state["validation_passed"] = False
        state["rejection_reason"] = "No specific medicine name was recognized in your request."
        state["agent_reply"] = state["rejection_reason"]
        return state
        
    # Check if medicine exists (exact name match, case insensitive)
    import re
    safe_name = re.escape(medicine_name)
    med = await db.medicines.find_one({"name": {"$regex": f"^{safe_name}$", "$options": "i"}})
    
    if not med:
        # Auto-create the medicine entry so the order can proceed
        # In a real pharmacy this would be reviewed, but for demo purposes we allow it
        import uuid
        med = {
            "product_id": f"MED-{uuid.uuid4().hex[:8].upper()}",
            "pzn": f"AUTO-{uuid.uuid4().hex[:6].upper()}",
            "name": medicine_name,
            "price": 0.0,
            "stock_level": 100,
            "reorder_threshold": 20,
            "prescription_required": False,
            "category": "General"
        }
        await db.medicines.insert_one(med)
        
    # Validate Prescription Policy
    rx_required = med.get("prescription_required", False)
    state["prescription_required"] = rx_required
    
    if rx_required:
        pat_id = state.get("patient_id")
        user = await db.users.find_one({"patient_id": pat_id})
        
        if not user or not user.get("has_valid_prescription"):
            # Route to Pharmacist instead of outright rejection
            from datetime import datetime
            import uuid
            
            queue_item = {
                "queue_id": str(uuid.uuid4()),
                "patient_id": pat_id,
                "medicine_name": med["name"],
                "quantity": entities.get("quantity", 1),
                "status": "pending_review",
                "reason": "Prescription Required",
                "created_at": datetime.utcnow()
            }
            await db.pharmacist_queue.insert_one(queue_item)
            
            state["validation_passed"] = False
            state["rejection_reason"] = f"{med['name']} requires a valid prescription. I've sent this request to our Pharmacist for a manual review. You will receive a notification once it is approved."
            state["agent_reply"] = state["rejection_reason"]
            return state
            
    state["validation_passed"] = True
    state["extracted_entities"]["medicine"] = med["name"]
    state["extracted_entities"]["product_id"] = med["product_id"]
    state["extracted_entities"]["pzn"] = med.get("pzn", "")
    
    # Use realistic price (fallback to lookup if DB has 0)
    db_price = float(med.get("price", 0))
    if db_price <= 0:
        from backend.services.pdf_service import get_medicine_price
        db_price = get_medicine_price(med["name"])
        # Update DB so future lookups are correct
        await db.medicines.update_one({"product_id": med["product_id"]}, {"$set": {"price": db_price}})
    state["extracted_entities"]["unit_price"] = db_price
    
    return state
