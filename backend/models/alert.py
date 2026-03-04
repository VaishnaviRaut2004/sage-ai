from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RefillAlert(BaseModel):
    alert_id: str
    patient_id: str
    patient_name: str
    medicine_name: str
    expected_runout_date: datetime
    days_remaining: int
    last_purchase_date: datetime
    notified: bool = False
    created_at: datetime = datetime.now()
