import requests

response = requests.post("http://localhost:8000/api/auth/login", json={
    "email": "patient@dhanvan.ai",
    "password": "patient123"
})
print("Status:", response.status_code)
print("Response:", response.json())
