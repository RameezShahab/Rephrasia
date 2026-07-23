import requests
import json
import sys

BASE_URL = "http://localhost:5173/api"
print(f"Testing Vite Proxy -> Flask Backend at {BASE_URL}\n")

def test_endpoint(name, method, path, payload=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    print(f"--- [QA] Testing {name} ---")
    print(f"Request: {method} {path}")
    if payload:
        print(f"Payload: {json.dumps(payload)}")
        
    try:
        if method == "POST":
            res = requests.post(url, json=payload, headers=headers)
        elif method == "GET":
            res = requests.get(url, headers=headers)
        
        print(f"Status: {res.status_code}")
        try:
            data = res.json()
            print(f"Response Body: {json.dumps(data, indent=2)}")
            return res.status_code, data
        except Exception:
            print(f"Response Text: {res.text}")
            return res.status_code, None
    except Exception as e:
        print(f"Error: {e}")
        return 500, None
    finally:
        print("-" * 40 + "\n")

# 1. Test Auth Register
status, auth_data = test_endpoint("Register", "POST", "/auth/register", {
    "name": "QA Tester",
    "email": "qa@example.com",
    "password": "securepassword123"
})

token = None
if status == 201 and auth_data and "token" in auth_data:
    token = auth_data["token"]
elif status == 409: # Already registered, let's login
    status, auth_data = test_endpoint("Login", "POST", "/auth/login", {
        "email": "qa@example.com",
        "password": "securepassword123"
    })
    if auth_data and "token" in auth_data:
        token = auth_data["token"]

# 2. Test Grammar Endpoint
test_endpoint("Grammar Check", "POST", "/grammar", {
    "text": "This are a test of the grammer system."
})

# 3. Test Rephrase (with mode)
test_endpoint("Rephrase (Mode: academic)", "POST", "/rephrase", {
    "text": "This is a simple test.",
    "mode": "academic"
})

# 4. Test Protected Route (Profile)
if token:
    test_endpoint("Get Profile", "GET", "/user/profile", token=token)
else:
    print("Skipping Profile test due to missing token.\n")
