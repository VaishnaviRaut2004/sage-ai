import asyncio
import os
import pandas as pd
import bcrypt
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Generate a REAL bcrypt hash for demo password '123456'
DEMO_PASSWORD_HASH = bcrypt.hashpw(b'123456', bcrypt.gensalt()).decode('utf-8')

async def main():
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.dhanvan
    
    # Clear collections
    await db.medicines.delete_many({})
    await db.users.delete_many({})
    await db.orders.delete_many({})
    await db.refill_alerts.delete_many({})
    print("Deleted old data.")

    # 0. Load Demo Accounts
    try:
        demo_patient = {
            "patient_id": "PAT000",
            "name": "Anna Müller",
            "email": "patient@dhanvan.ai",
            "password_hash": bcrypt.hashpw(b'patient123', bcrypt.gensalt()).decode('utf-8'),
            "age": 34,
            "gender": "Female",
            "role": "patient",
            "purchase_history": []
        }
        
        demo_pharmacist = {
            "patient_id": "PH000",
            "name": "Dr. Karl Lehmann",
            "email": "pharmacist@dhanvan.ai",
            "password_hash": bcrypt.hashpw(b'pharma123', bcrypt.gensalt()).decode('utf-8'),
            "role": "pharmacist",
            "purchase_history": []
        }
        await db.users.insert_many([demo_patient, demo_pharmacist])
        print("Inserted demo accounts.")
    except Exception as e:
        print(f"Error loading demo accounts: {e}")

    # 1. Load Medicine Master
    try:
        df_mm = pd.read_csv("data/medicine-master-enhanced.csv")
        medicines_to_insert = []
        for _, row in df_mm.iterrows():
            medicines_to_insert.append({
                "product_id": str(row.get("Product ID", "")),
                "name": str(row.get("Product Name", "")),
                "pzn": str(row.get("PZN", "")),
                "price": float(row.get("Price", 0.0)),
                "package_size_raw": str(row.get("Package Size", "")),
                "units_per_pack": int(row.get("Units Per Pack", 30)) if pd.notna(row.get("Units Per Pack")) else 30,
                "stock_level": int(row.get("Current Stock Level", 100)) if pd.notna(row.get("Current Stock Level")) else 100,
                "prescription_required": True if str(row.get("Prescription Required", "No")).lower() == "yes" else False,
                "reorder_threshold": int(row.get("Reorder Threshold", 20)) if pd.notna(row.get("Reorder Threshold")) else 20
            })
            
        if medicines_to_insert:
            await db.medicines.insert_many(medicines_to_insert)
            print(f"Inserted {len(medicines_to_insert)} medicines from master CSV.")
    except Exception as e:
        print(f"Error loading medicines: {e}")

    # 2. Load Consumer Order History
    try:
        # Skip the first 4 rows to reach the actual header row
        df_coh = pd.read_excel("data/Consumer Order History 1.xlsx", skiprows=4)
        
        users_dict = {}
        orders_to_insert = []
        
        for _, row in df_coh.iterrows():
            pat_id = str(row.get("Patient ID", ""))
            if not pat_id or pat_id == "nan": continue
            
            # Form users
            if pat_id not in users_dict:
                users_dict[pat_id] = {
                    "patient_id": pat_id,
                    "name": f"Patient {pat_id}",
                    "age": int(row.get("Patient Age", 30)) if pd.notna(row.get("Patient Age")) else None,
                    "gender": str(row.get("Patient Gender", "Unknown")),
                    "email": f"{pat_id.lower()}@example.com",
                    "password_hash": DEMO_PASSWORD_HASH,
                    "role": "patient",
                    "has_valid_prescription": False,
                    "purchase_history": []
                }
            
            # Find medicine ID from our newly inserted DB
            med_name = str(row.get("Product Name", ""))
            med_doc = await db.medicines.find_one({"name": med_name})
            product_id = med_doc["product_id"] if med_doc else ""
            pzn = med_doc["pzn"] if med_doc else ""
            rx_req = med_doc["prescription_required"] if med_doc else False
            
            qty = int(row.get("Quantity", 1)) if pd.notna(row.get("Quantity")) else 1
            tot = float(row.get("Total Price (EUR)", 0.0)) if pd.notna(row.get("Total Price (EUR)")) else 0.0
            
            p_date_raw = row.get("Purchase Date")
            if pd.notna(p_date_raw):
                p_date = pd.to_datetime(p_date_raw).to_pydatetime()
            else:
                p_date = datetime.now()
                
            order_id = f"ORD-{p_date.strftime('%Y%m%d')}-{str(len(orders_to_insert)+1).zfill(3)}"
            
            order_doc = {
                "order_id": order_id,
                "patient_id": pat_id,
                "patient_name": users_dict[pat_id]["name"],
                "medicine_name": med_name,
                "product_id": product_id,
                "pzn": pzn,
                "quantity": qty,
                "unit_price": (tot / qty) if qty > 0 else 0,
                "total_price": tot,
                "dosage_frequency": str(row.get("Dosage Frequency", "Once daily")),
                "purchase_date": p_date,
                "prescription_required": rx_req,
                "prescription_image_url": None,
                "status": "fulfilled",
                "delivery_address": {"street": "123 Main St", "city": "Sample City", "postal_code": "12345", "country": "Germany"},
                "payment_info": {"method": "card", "status": "paid", "transaction_id": "historical"},
                "invoice_id": None,
                "approved_by_pharmacist": "historical",
                "webhook_triggered": True,
                "created_at": p_date
            }
            
            result = await db.orders.insert_one(order_doc)
            users_dict[pat_id]["purchase_history"].append(result.inserted_id)
            orders_to_insert.append(order_doc)
            
        if users_dict:
            await db.users.insert_many(list(users_dict.values()))
            print(f"Inserted {len(users_dict)} patients.")
        print(f"Inserted {len(orders_to_insert)} historical orders.")
        
        # 3. Insert Dummy Refill Alerts for the Pharmacist Dashboard
        from datetime import timedelta
        alert1 = {
            "alert_id": "ALT-001",
            "patient_id": "PAT000",
            "patient_name": "Anna Müller",
            "medicine_name": "Ibuprofen 400mg",
            "expected_runout_date": datetime.now() + timedelta(days=2),
            "days_remaining": 2,
            "last_purchase_date": datetime.now() - timedelta(days=28),
            "notified": False
        }
        alert2 = {
            "alert_id": "ALT-002",
            "patient_id": "PAT123",
            "patient_name": "Patient PAT123",
            "medicine_name": "L-Thyroxin 50µg",
            "expected_runout_date": datetime.now() + timedelta(days=5),
            "days_remaining": 5,
            "last_purchase_date": datetime.now() - timedelta(days=50),
            "notified": True
        }
        await db.refill_alerts.insert_many([alert1, alert2])
        print("Inserted 2 dummy refill alerts.")

        
    except Exception as e:
        print(f"Error loading consumer orders: {e}")

if __name__ == "__main__":
    asyncio.run(main())
