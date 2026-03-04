from backend.graph_state import AgentState
from backend.database import db

async def inventory_agent_node(state: AgentState):
    if not state.get("validation_passed"):
        return state
        
    intent = state.get("intent_type")
    if intent != "ordering":
        return state
        
    entities = state.get("extracted_entities", {})
    product_id = entities.get("product_id")
    quantity = entities.get("quantity", 1)
    
    med = await db.medicines.find_one({"product_id": product_id})
    if not med:
         state["validation_passed"] = False
         state["rejection_reason"] = "Medicine not found during stock check."
         state["agent_reply"] = state["rejection_reason"]
         return state
         
    current_stock = med.get("stock_level", 0)
    if current_stock < quantity:
         state["validation_passed"] = False
         state["stock_sufficient"] = False
         state["rejection_reason"] = f"Insufficient stock for {med['name']}. We only have {current_stock} left."
         state["agent_reply"] = state["rejection_reason"]
         return state
         
    # Optimistic reservation - mark stock as sufficient, Action Agent does the final DB decrement.
    state["stock_sufficient"] = True
    
    if (current_stock - quantity) < med.get("reorder_threshold", 20):
        state["reorder_triggered"] = True
    else:
        state["reorder_triggered"] = False
        
    return state
