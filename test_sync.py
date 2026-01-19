#!/usr/bin/env python3
import requests

# Test POST /sync
print("=" * 60)
print("Testing POST /sync")
print("=" * 60)
try:
    with open(r"c:\Users\rainwater\Desktop\puantaj\puantaj_app\data\puantaj.db", "rb") as f:
        r = requests.post(
            "https://rainstaff.onrender.com/sync",
            headers={"X-API-KEY": "7487", "X-Region": "Ankara"},
            files={"db": f},
            timeout=15
        )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test GET /sync/download
print("\n" + "=" * 60)
print("Testing GET /sync/download")
print("=" * 60)
try:
    r = requests.get(
        "https://rainstaff.onrender.com/sync/download",
        headers={"X-API-KEY": "7487"},
        timeout=15
    )
    print(f"Status: {r.status_code}")
    print(f"Content-Length: {len(r.content)} bytes")
    print(f"Content-Type: {r.headers.get('content-type', 'unknown')}")
    if r.status_code == 200:
        print("✅ Download endpoint works!")
except Exception as e:
    print(f"Error: {e}")

# Test GET /sync/status
print("\n" + "=" * 60)
print("Testing GET /sync/status")
print("=" * 60)
try:
    r = requests.get(
        "https://rainstaff.onrender.com/sync/status",
        headers={"X-API-KEY": "7487"},
        timeout=15
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:300]}")
    if r.status_code == 200 and "success" in r.text:
        print("✅ Status endpoint works!")
    else:
        print("❌ Status endpoint not working (route not found)")
except Exception as e:
    print(f"Error: {e}")
