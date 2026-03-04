from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from backend.auth.dependencies import get_current_user
from backend.database import db
from backend.services.pdf_service import INVOICE_DIR, generate_invoice_pdf
import os

router = APIRouter()

@router.get("/{id}")
async def download_invoice(id: str, user = Depends(get_current_user)):
    file_path = os.path.join(INVOICE_DIR, f"{id}.pdf")
    
    # If PDF already exists on disk (consolidated or pre-generated), serve it directly
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=f"INV-{id}.pdf")
    
    # Otherwise, look up the order and generate on the fly
    order = await db.orders.find_one({"invoice_id": id})
    if not order:
        order = await db.orders.find_one({"order_id": id})
        if not order:
            raise HTTPException(status_code=404, detail="Invoice not found")
            
    if user["role"] == "patient" and order["patient_id"] != user["patient_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Generate on the fly
    pharmacist_name = "Dhanvan AI Pipeline"
    if order.get("approved_by_pharmacist"):
         ph = await db.users.find_one({"patient_id": order["approved_by_pharmacist"]})
         if ph: pharmacist_name = ph["name"]
    await generate_invoice_pdf(order, pharmacist_name)
        
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File generation failed")
        
    return FileResponse(file_path, media_type="application/pdf", filename=f"INV-{id}.pdf")

@router.post("/generate")
async def manual_generate(order_id: str, user = Depends(get_current_user)):
    order = await db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if user["role"] == "patient" and order["patient_id"] != user["patient_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    path = await generate_invoice_pdf(order)
    return {"message": "Invoice generated", "path": path}
