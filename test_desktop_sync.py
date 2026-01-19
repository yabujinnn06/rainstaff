#!/usr/bin/env python3
"""
Minimal desktop sync test
"""
import sys
import os

# Add app directory to path
sys.path.insert(0, r"C:\Users\rainwater\Desktop\puantaj\puantaj_app")

import db

# Test sync_with_server function
sync_url = "https://rainstaff.onrender.com"
api_key = "7487"
region = "Ankara"

print("=" * 60)
print("Testing Desktop Sync Functions")
print("=" * 60)

# Test 1: Upload + Download
print("\n1. Testing sync_with_server()...")
try:
    success, message = db.sync_with_server(sync_url, api_key, region)
    if success:
        print(f"   ✅ Sync successful: {message}")
    else:
        print(f"   ❌ Sync failed: {message}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Get server status
print("\n2. Testing get_sync_status()...")
try:
    status = db.get_sync_status(sync_url, api_key)
    if status:
        print(f"   ✅ Status: {status}")
    else:
        print(f"   ❌ Could not get status")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
