import requests
import uuid

# --- CONFIGURATION (Change these for your setup) ---
SERVER_URL = "http://localhost:8000" # Change to your backend server IP when running on Raspberry Pi
PATIENT_EMAIL = "prathmeshbavge@gmail.com"
PATIENT_PASSWORD = "patient123"

def send_scanned_prescription():
    print("1. Logging into the Pharmacy API...")
    
    # 1. Login to get the JWT Token
    login_res = requests.post(
        f"{SERVER_URL}/api/auth/login",
        json={"email": PATIENT_EMAIL, "password": PATIENT_PASSWORD}
    )
    
    if login_res.status_code != 200:
        print("Login failed:", login_res.text)
        return
        
    auth_data = login_res.json()
    token = auth_data["access_token"]
    patient_id = auth_data["patient_id"]
    
    print(f"✅ Logged in successfully as {patient_id}")
    
    # 2. Simulate OCR extracting text from an image
    # Imagine the ESP32 took a photo, passed it to this script, and Tesseract/EasyOCR read the text.
    extracted_text = "Paracetamol 500mg, 2 strips. Azithromycin 250mg, 1 strip."
    
    # 3. Format the message for the Pharmacy Chatbot Agent
    message_to_agent = f"I scanned this prescription text via my smart camera: {extracted_text}. Please order these for me."
    print("\n2. Sending OCR text to the Chat Agent...")
    print(f"Message: {message_to_agent}")
    
    # Generate a random session ID for this chat
    session_id = str(uuid.uuid4())
    
    # 4. Send the POST request to the Chat Endpoint
    chat_res = requests.post(
        f"{SERVER_URL}/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": message_to_agent,
            "session_id": session_id,
            "patient_id": patient_id
        }
    )
    
    if chat_res.status_code == 200:
        print("\n✅ Successfully sent to Chatbot Agent!")
        # The stream is chunked text. Let's just print the raw response buffer since we aren't using SSE here.
        print("\n--- Agent Reply ---")
        reply_buffer = ""
        for chunk in chat_res.iter_lines():
            if chunk:
                # The backend sends server-sent events (SSE) like data: {"reply": "..."}
                import json
                line = chunk.decode('utf-8')
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if "status" in data:
                            print(f"[{data['status']}]")
                        if "reply" in data:
                            reply_buffer += data["reply"]
                    except:
                        pass
        
        print("\nFinal Agent Message:")
        print(reply_buffer.strip())
    else:
        print("❌ Failed to send chat:", chat_res.text)

if __name__ == "__main__":
    send_scanned_prescription()
