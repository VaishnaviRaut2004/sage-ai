from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.database import connect_to_mongo, close_mongo_connection
from backend.auth.router import router as auth_router
from backend.routers.chat import router as chat_router
from backend.routers.prescriptions import router as prescriptions_router
from backend.routers.refills import router as refills_router
from backend.routers.invoices import router as invoices_router
from backend.routers.orders import router as orders_router
from backend.routers.medicines import router as medicines_router
from backend.routers.users import router as users_router
from backend.routers.pharmacist_chat import router as pharmacist_chat_router
from backend.execution.predict_refills import run_all_predictions
import os

app = FastAPI(title="Dhanvan-SageAI", version="1.0.1")
scheduler = AsyncIOScheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("./uploads/prescriptions", exist_ok=True)
os.makedirs("./invoices", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="./uploads"), name="uploads")

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(prescriptions_router, prefix="/api/prescriptions", tags=["prescriptions"])
app.include_router(refills_router, prefix="/api/refills", tags=["refills"])
app.include_router(invoices_router, prefix="/api/invoices", tags=["invoices"])
app.include_router(orders_router, prefix="/api/orders", tags=["orders"])
app.include_router(medicines_router, prefix="/api/medicines", tags=["medicines"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(pharmacist_chat_router, prefix="/api/pharmacist/chat", tags=["pharmacist_chat"])

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    scheduler.add_job(run_all_predictions, "interval", hours=1)
    scheduler.start()
    print("APScheduler started.")

@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    await close_mongo_connection()

@app.get("/health")
async def health_check():
    return {"status": "ok"}
