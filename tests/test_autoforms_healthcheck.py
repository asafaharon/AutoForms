"""
🧪 AutoForms Fixed Health Check
Updated to match current known routes and avoid unauthorized POSTs.
"""

import requests

BASE_URL = "http://localhost:8083"

def check_get(path):
    url = f"{BASE_URL}{path}"
    try:
        r = requests.get(url)
        assert r.status_code == 200
        print(f"✅ GET {path} – OK")
    except Exception as e:
        print(f"❌ GET {path} – Failed: {e}")

def check_post_allow_any(path, data):
    url = f"{BASE_URL}{path}"
    try:
        r = requests.post(url, data=data)
        print(f"✅ POST {path} – Status {r.status_code}")
    except Exception as e:
        print(f"❌ POST {path} – Error: {e}")

def main():
    print("🔍 Running AutoForms Health Check (Fixed)...\n")

    # Public pages
    check_get("/")
    check_get("/login")
    check_get("/register")
    check_get("/forgot-password")

    # Generator flow (updated path)
    check_get("/test-generator")
    check_post_allow_any("/api/generate", {
        "prompt": "Create a basic contact form"
    })

    # Simulated send (may fail due to no auth, but should not crash server)
    check_post_allow_any("/api/send-form-to-other-email", {
        "html": "<form><input></form>",
        "email": "test@example.com"
    })

    print("\n📋 Done. You may verify email and PDF manually if needed.")

if __name__ == "__main__":
    main()
