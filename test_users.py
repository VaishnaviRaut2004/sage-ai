import urllib.request
import urllib.error
import json
from backend.auth.jwt_handler import sign_jwt

token = sign_jwt('PH000', 'pharmacist', 'PH000')
req = urllib.request.Request(
    'http://localhost:8000/api/users', 
    headers={'Authorization': f'Bearer {token}'}
)

try:
    response = urllib.request.urlopen(req)
    print("Success:", response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
    print(e.read().decode())
except Exception as e:
    print("Other error:", str(e))
