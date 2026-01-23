import sqlite3
import os
import shutil
from datetime import datetime

# Setup
CLIENT_A = "client_a.db"
CLIENT_B = "client_b.db"
SERVER = "server.db"

FILES = [CLIENT_A, CLIENT_B, SERVER]

def cleanup():
    for f in FILES:
        if os.path.exists(f):
            os.remove(f)
        if os.path.exists(f + ".upload"):
            os.remove(f + ".upload")

def init_db(path):
    conn = sqlite3.connect(path)
    # Create basic tables
    conn.execute("CREATE TABLE IF NOT EXISTS timesheets (id INTEGER PRIMARY KEY, notes TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS deleted_records (id INTEGER PRIMARY KEY, table_name TEXT, record_id INTEGER, deleted_at TEXT)")
    conn.commit()
    conn.close()

def add_record(path, id, notes):
    conn = sqlite3.connect(path)
    conn.execute("INSERT OR REPLACE INTO timesheets (id, notes) VALUES (?, ?)", (id, notes))
    conn.commit()
    conn.close()

def delete_record(path, id):
    conn = sqlite3.connect(path)
    # Track deletion
    conn.execute("INSERT INTO deleted_records (table_name, record_id, deleted_at) VALUES (?, ?, ?)", 
                 ("timesheets", id, datetime.now().isoformat()))
    # Delete actual
    conn.execute("DELETE FROM timesheets WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def get_record(path, id):
    conn = sqlite3.connect(path)
    cursor = conn.execute("SELECT * FROM timesheets WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    return row

def is_deleted_tracked(path, id):
    conn = sqlite3.connect(path)
    cursor = conn.execute("SELECT * FROM deleted_records WHERE table_name='timesheets' AND record_id=?", (id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def merge_logic(incoming_path, master_path):
    # This mimics the _merge_databases logic in server/app.py
    incoming = sqlite3.connect(incoming_path)
    master = sqlite3.connect(master_path)
    
    # 1. Get incoming deletions
    deleted_in_incoming = set()
    try:
        cur = incoming.execute("SELECT table_name, record_id FROM deleted_records")
        for row in cur.fetchall():
            deleted_in_incoming.add((row[0], row[1]))
    except: pass
    
    # 2. Apply to master
    for table, rid in deleted_in_incoming:
        if table == "timesheets":
            master.execute("DELETE FROM timesheets WHERE id = ?", (rid,))
            master.execute("INSERT OR IGNORE INTO deleted_records (table_name, record_id, deleted_at) VALUES (?, ?, ?)", 
                           (table, rid, datetime.now().isoformat()))
            
    master.commit()
    
    # 3. Get master deletions
    deleted_in_master = set()
    cur = master.execute("SELECT table_name, record_id FROM deleted_records")
    for row in cur.fetchall():
        deleted_in_master.add((row[0], row[1]))
        
    all_deleted = deleted_in_incoming | deleted_in_master
    
    # 4. Merge new records (skip if deleted)
    cur = incoming.execute("SELECT id, notes FROM timesheets")
    for row in cur.fetchall():
        rid = row[0]
        if ("timesheets", rid) in all_deleted:
            print(f"DEBUG: Skipping merge of Record {rid} because it is marked as deleted.")
            continue
        master.execute("INSERT OR REPLACE INTO timesheets (id, notes) VALUES (?, ?)", row)
        
    master.commit()
    incoming.close()
    master.close()

def run_test():
    print("--- STARTING SYNC LOGIC VERIFICATION ---")
    cleanup()
    
    # 1. Initialize
    print("1. Initializing DBs...")
    for f in FILES:
        init_db(f)
        
    # 2. Add Record 100 to all (simulating existing sync state)
    print("2. Adding Record 100 to Client A, Client B, Server...")
    add_record(CLIENT_A, 100, "Original Note")
    add_record(CLIENT_B, 100, "Original Note")
    add_record(SERVER, 100, "Original Note")
    
    # Verify state
    assert get_record(CLIENT_A, 100) is not None
    assert get_record(CLIENT_B, 100) is not None
    
    # 3. Client A deletes Record 100
    print("3. Client A deletes Record 100...")
    delete_record(CLIENT_A, 100)
    assert get_record(CLIENT_A, 100) is None
    assert is_deleted_tracked(CLIENT_A, 100) is True
    
    # 4. Client A Syncs (Uploads to Server)
    print("4. Client A Syncs (Upload to Server)...")
    shutil.copy(CLIENT_A, CLIENT_A + ".upload")
    merge_logic(CLIENT_A + ".upload", SERVER)
    os.remove(CLIENT_A + ".upload")
    
    # Verify Server deleted it
    print("   Verifying Server state...")
    svr_rec = get_record(SERVER, 100)
    if svr_rec is None:
        print("   SUCCESS: Record 100 deleted from Server.")
    else:
        print("   FAILURE: Record 100 stil exists on Server.")
        exit(1)
        
    assert is_deleted_tracked(SERVER, 100) is True
    
    # 5. Client B Syncs 
    # Scenario: Client B has Record 100 (NOT deleted). 
    # Only uploads timesheet row. NO deleted_record entry for 100.
    print("5. Client B Syncs (Upload)...")
    shutil.copy(CLIENT_B, CLIENT_B + ".upload")
    merge_logic(CLIENT_B + ".upload", SERVER)
    os.remove(CLIENT_B + ".upload")
    
    # Verify Server state - Should STILL be deleted
    # The merge logic should SKIP inserting Record 100 from Client B
    # because it is in Server's deleted_records.
    print("   Verifying Server state after Client B upload...")
    svr_rec = get_record(SERVER, 100)
    if svr_rec is None:
        print("   SUCCESS: Record 100 remained deleted on Server (Zombie prevented).")
    else:
        print("   FAILURE: Record 100 reappeared on Server!")
        exit(1)
        
    # 6. Client B Downloads
    print("6. Client B Downloads (Server -> Client B)...")
    # Simulation: Client B replaces local DB with Server DB
    shutil.copy(SERVER, CLIENT_B)
    
    # Verify Client B
    print("   Verifying Client B state...")
    cli_b_rec = get_record(CLIENT_B, 100)
    if cli_b_rec is None:
        print("   SUCCESS: Record 100 is gone from Client B.")
    else:
        print("   FAILURE: Record 100 still exists on Client B.")
        exit(1)
        
    cleanup()
    print("--- VERIFICATION COMPLETE: ALL TESTS PASSED ---")

if __name__ == "__main__":
    run_test()
