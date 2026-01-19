#!/usr/bin/env python3
"""Fix duplicate /health endpoint in app.py"""

app_py_path = r"C:\Users\rainwater\Desktop\puantaj\server\app.py"

with open(app_py_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find and remove the duplicate health endpoint (the new one we added)
# Keep the original one, remove our added one

duplicate_endpoint = '''
@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "rainstaff",
        "timestamp": datetime.now(LOCAL_TZ).isoformat()
    }, 200

'''

if duplicate_endpoint in content:
    content = content.replace(duplicate_endpoint, "")
    print("✅ Duplicate /health endpoint removed")
else:
    print("⚠️ Could not find exact duplicate to remove")

# Write back
with open(app_py_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ app.py fixed!")
print("   → Duplicate @app.route('/health') removed")
print("   → Original health endpoint kept")
