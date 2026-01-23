"""Fix admin password in database"""
import puantaj_db as db

# Initialize database
db.init_db()

# Check current admin user
user = db.get_user('admin')
if user:
    print(f"Current admin hash: {user['password_hash']}")
else:
    print("Admin user NOT FOUND")

# Expected hash for password "748774"
expected = db.hash_password("748774")
print(f"Expected hash: {expected}")

# Update admin password
with db.get_conn() as conn:
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE username = 'admin';",
        (expected,)
    )
    print("Admin password updated!")

# Verify
user = db.get_user('admin')
if user:
    print(f"New admin hash: {user['password_hash']}")
    if db.verify_password("748774", user['password_hash']):
        print("✓ Password verification SUCCESS!")
    else:
        print("✗ Password verification FAILED!")
