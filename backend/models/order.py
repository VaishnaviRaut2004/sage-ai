from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeliveryAddress(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str

class PaymentInfo(BaseModel):
    method: str
    status: str
    transaction_id: Optional[str] = None

class Order(BaseModel):
    order_id: str
    patient_id: str
    patient_name: str
    medicine_name: str
    product_id: str
    pzn: str
    quantity: int
    unit_price: float
    total_price: float
    dosage_frequency: str
    purchase_date: datetime
    prescription_required: bool
    prescription_image_url: Optional[str] = None
    status: str
    delivery_address: DeliveryAddress
    payment_info: PaymentInfo
    invoice_id: Optional[str] = None
    approved_by_pharmacist: Optional[str] = None
    webhook_triggered: bool = False
    langsmith_trace_id: Optional[str] = None
    created_at: datetime
