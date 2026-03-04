import asyncio
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from backend.pharmacist_graph import pharmacist_supervisor
import time

router = APIRouter()

class PharmacistChatRequest(BaseModel):
    message: str
    session_id: str

@router.post("")
async def pharmacist_chat_endpoint(req: PharmacistChatRequest):
    if not req.message.strip():
        return {"reply": "How can I help you today?"}
        
    inputs = {"messages": [HumanMessage(content=req.message)]}
    config = {"configurable": {"thread_id": req.session_id}}
    
    try:
        final_state = await pharmacist_supervisor.ainvoke(inputs, config=config)
        messages = final_state.get("messages", [])
        if not messages:
            agent_response = "I encountered an error processing that request."
        else:
            agent_response = messages[-1].content
            
        return {"reply": agent_response}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Pharmacist Agent Error: {e}")
        raise HTTPException(status_code=500, detail="The Pharmacist Assistant encountered an error.")
