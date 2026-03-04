from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from backend.auth.dependencies import require_patient
from backend.graph import app_graph
from backend.database import db
from langsmith import traceable
import os
from openai import AsyncOpenAI
import uuid

router = APIRouter()
async_openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), user = Depends(require_patient)):
    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
            
        with open(temp_path, "rb") as audio_file:
            import openai
            sync_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 
            transcript = sync_client.audio.transcriptions.create(
              model="whisper-1", 
              file=audio_file, 
              response_format="text"
            )
        return {"text": transcript}
    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail="Voice transcription failed. You might need to check API keys.")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

class ChatRequest(BaseModel):
    message: str
    session_id: str
    patient_id: str

@router.post("") # mounts at /api/chat
@traceable(run_type="chain", name="dhanvan_order_pipeline")
async def chat_endpoint(req: ChatRequest, user = Depends(require_patient)):
    # Verify patient_id matches JWT to prevent ID spoofing
    if req.patient_id != user["patient_id"]:
        raise HTTPException(status_code=403, detail="Cannot chat as another patient")
        
    from langsmith.run_helpers import get_current_run_tree
    rt = get_current_run_tree()
    trace_url = getattr(rt, "url", None) or (rt.get_url() if hasattr(rt, "get_url") else None)
    trace_id = str(rt.id) if rt else None

    # Fetch chat history
    history_cursor = db.messages.find({"session_id": req.session_id}).sort("timestamp", 1)
    chat_history = []
    async for msg in history_cursor:
        chat_history.append({"role": msg["role"], "content": msg["content"]})

    # Load most recent prescription extraction for this patient
    recent_rx = await db.prescriptions.find_one(
        {"patient_id": req.patient_id},
        sort=[("timestamp", -1)]
    )
    prescription_context = ""
    if recent_rx and recent_rx.get("extraction"):
        rx = recent_rx["extraction"]
        meds_list = ", ".join([f"{m['name']} (dosage: {m.get('dosage','N/A')}, qty: {m.get('quantity',1)}, freq: {m.get('frequency','N/A')})" for m in rx.get("medicines", [])])
        prescription_context = f"The patient has a valid prescription from Dr. {rx.get('doctor_name','Unknown')}. Medicines on the prescription: {meds_list}. When the patient says 'order it' or 'order these', use these medicines directly."

    initial_state = {
        "session_id": req.session_id,
        "patient_id": req.patient_id,
        "input_text": req.message,
        "chat_history": chat_history,
        "prescription_context": prescription_context,
        "intent_type": "",
        "extracted_entities": {},
        "validation_passed": False,
        "rejection_reason": "",
        "prescription_required": False,
        "patient_has_rx": False,
        "stock_sufficient": False,
        "reorder_triggered": False,
        "order_id": "",
        "invoice_url": "",
        "agent_reply": "",
        "langsmith_trace_id": trace_id,
        "langsmith_trace_url": trace_url
    }
    
    # Run the graph
    result = await app_graph.ainvoke(initial_state, config={"run_name": "dhanvan_order_pipeline"})
    
    agent_reply = result.get("agent_reply", "Processed")
    
    # Save messages to DB for memory
    import time
    await db.messages.insert_many([
        {
            "session_id": req.session_id,
            "patient_id": req.patient_id,
            "role": "user",
            "content": req.message,
            "timestamp": int(time.time() * 1000)
        },
        {
            "session_id": req.session_id,
            "patient_id": req.patient_id,
            "role": "assistant",
            "content": agent_reply,
            "timestamp": int(time.time() * 1000) + 1
        }
    ])
    
    return {
        "reply": agent_reply,
        "order_draft": result.get("extracted_entities", {}) if result.get("validation_passed") else {},
        "intent": result.get("intent_type") if result.get("validation_passed") else "error",
        "order_id": result.get("order_id"),
        "trace_url": trace_url
    }
