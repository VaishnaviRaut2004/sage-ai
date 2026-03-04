from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from backend.auth.jwt_handler import decode_jwt, SECRET_KEY
from backend.database import db
import jwt
import time

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    return {
        "patient_id": payload.get("patient_id"),
        "staff_id": payload.get("staff_id"),
        "role": payload.get("role")
    }

def require_pharmacist(user = Depends(get_current_user)):
    if user["role"] != "pharmacist":
        raise HTTPException(status_code=403, detail="Pharmacist access required")
    return user

def require_patient(user = Depends(get_current_user)):
    if user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")
    return user
