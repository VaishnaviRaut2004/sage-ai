from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from backend.auth.dependencies import require_patient
from backend.database import db
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import base64
import time

router = APIRouter()

# 1. Define strict deterministic schema (Layer 2 Orchestration)
class MedicineExtraction(BaseModel):
    name: str = Field(description="Name of the medicine")
    dosage: Optional[str] = Field(None, description="Dosage amount (e.g. 500mg)")
    quantity: Optional[int] = Field(None, description="Quantity prescribed")
    frequency: Optional[str] = Field(None, description="How often to take it (e.g. twice daily)")

class PrescriptionExtraction(BaseModel):
    medicines: List[MedicineExtraction] = Field(description="List of extracted medicines")
    doctor_name: Optional[str] = Field(None, description="Name of the prescribing doctor")
    date_issued: Optional[str] = Field(None, description="Date issued in ISO format")
    patient_name: Optional[str] = Field(None, description="Name of the patient")
    is_valid_prescription: bool = Field(description="True if it looks like a valid medical prescription, false otherwise")

# Bind LLM to schema
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(PrescriptionExtraction)

UPLOAD_DIR = os.getenv("UPLOAD_STORAGE_PATH", "./uploads/prescriptions")
os.makedirs(UPLOAD_DIR, exist_ok=True)

PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a pharmacy parser. You will receive raw, messy text extracted from an OCR scanner reading a prescription image. Map this unstructured text into the exact requested JSON schema. If fields are missing (like date or doctor), leave them null. Be careful to reconstruct split medicine names. Respond ONLY with the parsed details."),
    ("user", "OCR Raw Text:\n\n{ocr_text}")
])

@router.post("/upload")
async def upload_prescription(file: UploadFile = File(...), user = Depends(require_patient)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")
        
    contents = await file.read()
    filename = f"{user['patient_id']}_{int(time.time())}.{file.filename.split('.')[-1]}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    with open(filepath, "wb") as f:
        f.write(contents)
        
    try:
        # Convert image to base64 for the Vision LLM
        base64_image = base64.b64encode(contents).decode("utf-8")
        
        # Determine mime type from file extension
        ext = file.filename.split('.')[-1].lower()
        mime = f"image/{'jpeg' if ext in ('jpg','jpeg') else ext}"
        
        print(f"[Vision OCR] Sending {len(contents)} byte image to GPT-4o-mini Vision...")
        
        # Send directly to Vision LLM with structured output
        messages = [
            ("system", 
             "You are an expert pharmacy prescription parser. Look at the attached image of a medical prescription. "
             "Carefully read ALL text visible in the image including medicine names, dosages, quantities, frequencies, "
             "doctor name, patient name, and date. Map everything into the exact required JSON schema. "
             "If fields are missing, leave them null. Be very thorough - extract every medicine you can see."),
            ("human", [
                {"type": "text", "text": "Extract all prescription details from this image:"},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64_image}"}}
            ])
        ]
        
        extraction: PrescriptionExtraction = await structured_llm.ainvoke(messages)
        print(f"[Vision OCR] Extracted: {extraction.model_dump()}")
        
        # Include ALL extracted medicines, flag which ones are in the DB catalog
        validated_meds = []
        for m in extraction.medicines:
            med_name = m.name
            if med_name:
                db_med = await db.medicines.find_one({"name": {"$regex": f"^{med_name}$", "$options": "i"}})
                validated_meds.append({
                    "name": db_med["name"] if db_med else m.name,
                    "dosage": m.dosage,
                    "quantity": m.quantity or 1,
                    "frequency": m.frequency,
                    "in_catalog": bool(db_med)
                })
        
        final_data = {
            "medicines": validated_meds,
            "doctor_name": extraction.doctor_name,
            "date_issued": extraction.date_issued,
            "patient_name": extraction.patient_name,
            "is_valid_prescription": extraction.is_valid_prescription,
            "image_url": f"/uploads/prescriptions/{filename}"
        }
        
        # Guard: If no medicines were found, it's likely a blank/invalid page
        if not final_data["medicines"] and not extraction.is_valid_prescription:
            # Delete the uploaded dummy file so it doesn't clutter storage
            if os.path.exists(filepath):
                os.remove(filepath)
            raise HTTPException(
                status_code=400, 
                detail="No medical information could be extracted. Please upload a valid prescription."
            )
        
        # Save extraction to MongoDB so the chat agent can reference it
        import time as _time
        await db.prescriptions.insert_one({
            "patient_id": user["patient_id"],
            "extraction": final_data,
            "timestamp": int(_time.time() * 1000)
        })
        
        # Update user record
        if extraction.is_valid_prescription:
             await db.users.update_one({"patient_id": user["patient_id"]}, {"$set": {"has_valid_prescription": True}})
             
        return final_data
    except Exception as e:
        print(f"Prescription parsing pipeline failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse prescription")

@router.post("/order-all")
async def order_all_prescription_medicines(user = Depends(require_patient)):
    """Batch-order ALL medicines from the patient's most recent prescription in one click."""
    from datetime import datetime
    import uuid as _uuid
    
    # Load the most recent prescription
    recent_rx = await db.prescriptions.find_one(
        {"patient_id": user["patient_id"]},
        sort=[("timestamp", -1)]
    )
    
    if not recent_rx or not recent_rx.get("extraction"):
        raise HTTPException(status_code=404, detail="No recent prescription found. Please upload one first.")
    
    rx = recent_rx["extraction"]
    medicines = rx.get("medicines", [])
    
    if not medicines:
        raise HTTPException(status_code=400, detail="No medicines found in the prescription.")
    
    patient = await db.users.find_one({"patient_id": user["patient_id"]})
    orders_created = []
    
    for med_item in medicines:
        med_name = med_item.get("name")
        qty = med_item.get("quantity", 1)
        
        if not med_name:
            continue
        
        # Find or auto-create in catalog  
        import re
        safe_name = re.escape(med_name)
        med = await db.medicines.find_one({"name": {"$regex": f"^{safe_name}$", "$options": "i"}})
        
        if not med:
            med = {
                "product_id": f"MED-{_uuid.uuid4().hex[:8].upper()}",
                "pzn": f"AUTO-{_uuid.uuid4().hex[:6].upper()}",
                "name": med_name,
                "price": 0.0,
                "stock_level": 100,
                "reorder_threshold": 20,
                "prescription_required": False,
                "category": "General"
            }
            await db.medicines.insert_one(med)
        
        # Get realistic price BEFORE creating order doc
        from backend.services.pdf_service import get_medicine_price
        real_price = get_medicine_price(med["name"])
        
        # Update DB medicine price if it was 0
        if float(med.get("price", 0)) <= 0:
            await db.medicines.update_one({"product_id": med["product_id"]}, {"$set": {"price": real_price}})
        
        frequency = med_item.get("frequency", "As prescribed")
        
        # Create the order with CORRECT price
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{_uuid.uuid4().hex[:4].upper()}"
        
        order_doc = {
            "order_id": order_id,
            "patient_id": user["patient_id"],
            "patient_name": patient["name"] if patient else "Unknown",
            "medicine_name": med["name"],
            "product_id": med["product_id"],
            "pzn": med.get("pzn", ""),
            "quantity": qty,
            "unit_price": real_price,
            "total_price": real_price * qty,
            "dosage_frequency": frequency,
            "purchase_date": datetime.now(),
            "prescription_required": False,
            "prescription_image_url": rx.get("image_url"),
            "status": "pending",
            "doctor_name": rx.get("doctor_name"),
            "delivery_address": {
                "street": "Shivaji Chawk",
                "city": "Latur",
                "postal_code": "413512",
                "country": "India"
            },
            "invoice_id": order_id,
            "created_at": datetime.now()
        }
        
        await db.orders.insert_one(order_doc)
        
        # Decrement stock
        await db.medicines.update_one(
            {"product_id": med["product_id"]},
            {"$inc": {"stock_level": -qty}}
        )
        
        orders_created.append({
            "order_id": order_id,
            "invoice_id": order_id,
            "medicine": med["name"],
            "quantity": qty,
            "frequency": frequency,
            "unit_price": real_price,
            "total": real_price * qty
        })
    
    # Generate ONE consolidated invoice for all medicines
    from backend.services.pdf_service import generate_consolidated_invoice
    invoice_path, consolidated_invoice_id = await generate_consolidated_invoice(
        orders=orders_created,
        patient_info={"name": patient.get("name", "N/A"), "patient_id": user["patient_id"], "address": patient.get("delivery_address", {})},
        rx_info=rx,
    )
    
    grand_total = sum(o["total"] for o in orders_created)
    
    return {
        "message": f"Successfully ordered {len(orders_created)} medicines from your prescription!",
        "orders": orders_created,
        "doctor": rx.get("doctor_name"),
        "consolidated_invoice_id": consolidated_invoice_id,
        "grand_total": grand_total
    }

@router.get("/{id}")
async def get_prescription(id: str, user = Depends(require_patient)):
    return {"status": "Not implemented"}
