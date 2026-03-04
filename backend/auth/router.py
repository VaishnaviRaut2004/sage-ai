from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import bcrypt
from backend.database import db
from backend.auth.jwt_handler import sign_jwt
from backend.models.user import User
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

class RegisterPatientRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: int
    gender: str
    
class RegisterPharmacistRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    pharmacist_code: str

@router.post("/register")
async def register(patient_req: RegisterPatientRequest = None, pharma_req: RegisterPharmacistRequest = None):
    pass

@router.post("/register/patient")
async def register_patient(req: RegisterPatientRequest):
    if await db.users.find_one({"email": req.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    num_users = await db.users.count_documents({"role": "patient"})
    pat_id = f"PAT{str(num_users + 1).zfill(3)}"
    
    new_user = User(
        patient_id=pat_id,
        name=req.name,
        email=req.email,
        password_hash=hash_password(req.password),
        age=req.age,
        gender=req.gender,
        role="patient",
        purchase_history=[]
    )
    
    await db.users.insert_one(new_user.model_dump())
    return {"message": "Patient registered successfully", "patient_id": pat_id}

@router.post("/register/pharmacist")
async def register_pharmacist(req: RegisterPharmacistRequest):
    expected_code = os.getenv("PHARMACIST_REGISTRATION_CODE", "PHARMA-2024-SECRET")
    if req.pharmacist_code != expected_code:
        raise HTTPException(status_code=403, detail="Invalid pharmacist registration code")
        
    if await db.users.find_one({"email": req.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    num_pharma = await db.users.count_documents({"role": "pharmacist"})
    staff_id = f"PH{str(num_pharma + 1).zfill(3)}"
    
    new_user = User(
        patient_id=staff_id,
        name=req.name,
        email=req.email,
        password_hash=hash_password(req.password),
        role="pharmacist",
        purchase_history=[]
    )
    
    await db.users.insert_one(new_user.model_dump())
    return {"message": "Pharmacist registered successfully", "staff_id": staff_id}

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(req: LoginRequest):
    user = await db.users.find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    # Handle the mock hashes from data_loader or native bcrypt hashes
    try:
        is_valid = verify_password(req.password, user["password_hash"])
    except (ValueError, Exception):
        is_valid = False

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if user["role"] == "patient":
        token = sign_jwt(user["patient_id"], "patient")
    else:
        token = sign_jwt(None, "pharmacist", user["patient_id"])
        
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "patient_id": user.get("patient_id", ""),
        "name": user.get("name", "")
    }
