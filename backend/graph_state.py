from typing import TypedDict, Annotated, List, Dict, Any
from operator import add

class AgentState(TypedDict):
    session_id: str
    patient_id: str
    input_text: str
    chat_history: List[Dict[str, str]] # [{'role': 'user'|'assistant', 'content': '...'}]
    prescription_context: str # Recent prescription extraction context for the chat agent
    
    # Intent extraction
    intent_type: str # 'ordering', 'refill_inquiry', 'general', 'prescription_upload'
    extracted_entities: Dict[str, Any] # { "medicine": "...", "quantity": 1 }
    
    # Validation from Pharmacy Design
    validation_passed: bool
    rejection_reason: str
    prescription_required: bool
    patient_has_rx: bool
    
    # Inventory
    stock_sufficient: bool
    reorder_triggered: bool
    
    # Action
    order_id: str
    invoice_url: str
    
    # Final Output
    agent_reply: str
