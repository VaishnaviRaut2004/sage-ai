from pydantic import BaseModel, EmailStr
from typing import Optional, List

class User(BaseModel):
    patient_id: Optional[str] = None
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    email: EmailStr
    password_hash: str
    role: str = "patient" # or "pharmacist"
    has_valid_prescription: bool = False
    purchase_history: List[str] = []
