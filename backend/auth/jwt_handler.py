import time
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-very-long-random-secret-key-here")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRES_IN = int(os.getenv("JWT_EXPIRY_HOURS", 24)) * 3600

def sign_jwt(patient_id: str, role: str, staff_id: str = None) -> str:
    payload = {
        "patient_id": patient_id,
        "staff_id": staff_id,
        "role": role,
        "exp": time.time() + EXPIRES_IN
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_jwt(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token if decoded_token["exp"] >= time.time() else None
    except:
        return None
