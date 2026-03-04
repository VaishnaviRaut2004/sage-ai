import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
SENDER_EMAIL = os.getenv("RESEND_SENDER_EMAIL", "onboarding@resend.dev")

import asyncio

async def send_order_confirmation(email: str, order: dict, invoice_path: str = None):
    """Sends an order confirmation email using Resend API."""
    if not resend.api_key:
        print("RESEND_API_KEY not configured. Skipping email confirmation.")
        return
        
    order_id = order.get("order_id")
    medicine_name = order.get("medicine_name")
    qty = order.get("quantity")
    total = order.get("total_price")
    
    html_content = f"""
    <h2>Order Confirmation - Dhanvan-SageAI</h2>
    <p>Dear {order.get('patient_name', 'Patient')},</p>
    <p>Your order <strong>{order_id}</strong> has been successfully placed and approved.</p>
    <h3>Order Details:</h3>
    <ul>
        <li><strong>Order ID:</strong> {order['order_id']}</li>
        <li><strong>Medicine:</strong> {order['medicine_name']}x {order['quantity']}</li>
        <li><strong>Total:</strong> ₹{total:.2f}</li>
    </ul>
    <p>Your invoice has been generated and is attached to this email.</p>
    <p>Thank you for choosing Dhanvan Pharmacy.</p>
    """
    
    attachments = []
    if invoice_path and os.path.exists(invoice_path):
        with open(invoice_path, "rb") as f:
            pdf_content = f.read()
            attachments.append({
                "filename": f"Invoice_{order_id}.pdf",
                "content": list(pdf_content)
            })
            
    payload = {
        "from": f"Dhanvan-SageAI Pharmacy <{SENDER_EMAIL}>",
        "to": [email],
        "subject": f"Order Confirmation: {order_id}",
        "html": html_content
    }
    
    if attachments:
        payload["attachments"] = attachments
        
    try:
        email_response = await asyncio.to_thread(resend.Emails.send, payload)
        print(f"Email sent successfully. ID: {email_response.get('id')}")
        return email_response
    except Exception as e:
        print(f"Failed to send email: {e}")
        return None

async def send_refill_alert_email(email: str, alert_doc: dict):
    """Sends a refill alert email to the patient."""
    if not resend.api_key:
        print("RESEND_API_KEY not configured. Skipping refill email.")
        return
        
    medicine_name = alert_doc.get("medicine_name")
    days = alert_doc.get("days_remaining")
    
    html_content = f"""
    <h2>Refill Reminder from Dhanvan-SageAI</h2>
    <p>Dear {alert_doc.get('patient_name', 'Patient')},</p>
    <p>This is an automated reminder that your prescription for <strong>{medicine_name}</strong> is expected to run out in <strong>{days} days</strong>.</p>
    <p>Please log in to your Patient Dashboard to request a refill so you do not run out of your medication.</p>
    <br/>
    <p>Stay healthy,<br/>Dhanvan Pharmacy Team</p>
    """
    
    payload = {
        "from": f"Dhanvan-SageAI Pharmacy <{SENDER_EMAIL}>",
        "to": [email],
        "subject": f"Refill Reminder: {medicine_name}",
        "html": html_content
    }
    
    try:
        email_response = await asyncio.to_thread(resend.Emails.send, payload)
        print(f"Refill email sent successfully. ID: {email_response.get('id')}")
        return email_response
    except Exception as e:
        print(f"Failed to send refill email: {e}")
        return None
