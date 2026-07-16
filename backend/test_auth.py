import sys
import httpx

BASE_URL = "http://localhost:8000/api/v1/auth"

def run_tests():
    client = httpx.Client()
    
    test_user = {
        "email": "testuser@example.com",
        "username": "testuser",
        "display_name": "Test User",
        "password": "supersecurepassword123"
    }
    
    # 1. Register User
    print("Testing /register...")
    try:
        res = client.post(f"{BASE_URL}/register", json=test_user)
        print("Register Status:", res.status_code)
        if res.status_code == 201:
            print("Register Response:", res.json())
        elif res.status_code == 409:
            print("User already registered. Continuing...")
        else:
            print("Register failed:", res.text)
            sys.exit(1)
    except Exception as e:
        print("Connection failed:", e)
        sys.exit(1)
        
    # 2. Login User
    print("\nTesting /login...")
    res = client.post(f"{BASE_URL}/login", json={
        "email": test_user["email"],
        "password": test_user["password"]
    })
    print("Login Status:", res.status_code)
    if res.status_code != 200:
        print("Login failed:", res.text)
        sys.exit(1)
        
    tokens = res.json()
    print("Tokens acquired:", list(tokens.keys()))
    access_token = tokens["access_token"]
    
    # 3. Fetch User profile
    print("\nTesting /me...")
    headers = {"Authorization": f"Bearer {access_token}"}
    res = client.get(f"{BASE_URL}/me", headers=headers)
    print("Get profile Status:", res.status_code)
    if res.status_code != 200:
        print("Fetch profile failed:", res.text)
        sys.exit(1)
        
    profile = res.json()
    print("Profile Details:", profile)
    assert profile["email"] == test_user["email"]
    assert profile["username"] == test_user["username"]
    print("\nAll authentication tests passed successfully!")

if __name__ == "__main__":
    run_tests()
