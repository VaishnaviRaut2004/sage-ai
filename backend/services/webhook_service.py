import httpx
import os
import datetime

async def fire_fulfillment_webhook(order_doc: dict):
    webhook_url = os.getenv("FULFILLMENT_WEBHOOK_URL")
    if not webhook_url:
        print("No FULFILLMENT_WEBHOOK_URL set!")
        return
        
    payload = {
        "event": "order_placed",
        "order_id": order_doc["order_id"],
        "patient_name": order_doc["patient_name"],
        "patient_id": order_doc["patient_id"],
        "delivery_address": order_doc["delivery_address"],
        "medicines": [{
            "name": order_doc["medicine_name"],
            "pzn": order_doc["pzn"],
            "quantity": order_doc["quantity"],
            "unit_price": order_doc["unit_price"]
        }],
        "total_price_eur": order_doc["total_price"],
        "invoice_url": f"https://dhanvan-sageai.onrender.com/api/invoices/{order_doc['invoice_id']}.pdf" if order_doc.get("invoice_id") else "",
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(webhook_url, json=payload)
        except Exception as e:
            print(f"Webhook error: {e}")

async def fire_procurement_webhook(medicine_name: str, pzn: str, current_stock: int, threshold: int):
    webhook_url = os.getenv("PROCUREMENT_WEBHOOK_URL")
    if not webhook_url:
        print("No PROCUREMENT_WEBHOOK_URL set!")
        return
        
    payload = {
        "event": "reorder_needed",
        "medicine_name": medicine_name,
        "pzn": pzn,
        "current_stock": current_stock,
        "reorder_threshold": threshold,
        "suggested_reorder_quantity": 100,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(webhook_url, json=payload)
        except Exception as e:
            print(f"Procurement webhook error: {e}")
