import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "test.db")
print("=" * 60)
print(f"DATABASE FILE: {os.path.abspath(db_path)}")
print("=" * 60)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Users
print("\n--- [TABLE: users] ---")
users = cursor.execute("SELECT id, email, role, tokens, created_at FROM users").fetchall()
if not users:
    print("No users found.")
else:
    for u in users:
        print(f"User ID: {u['id']} | Email: {u['email']} | Role: {u['role']} | Credits: {u['tokens']}")

# 2. Conversations
print("\n--- [TABLE: conversations] ---")
convs = cursor.execute("SELECT id, title, created_at FROM conversations ORDER BY created_at DESC LIMIT 5").fetchall()
if not convs:
    print("No conversations found.")
else:
    for c in convs:
        print(f"ID: {c['id'][:8]}... | Title: '{c['title']}' | Created: {c['created_at']}")

# 3. Messages
print("\n--- [TABLE: messages] ---")
msgs = cursor.execute("SELECT role, provider, model, content, created_at FROM messages ORDER BY created_at DESC LIMIT 6").fetchall()
if not msgs:
    print("No messages found.")
else:
    for m in reversed(msgs):
        snippet = m['content'][:60].replace('\n', ' ')
        print(f"[{m['role'].upper()}] ({m['provider'] or 'N/A'}/{m['model'] or 'N/A'}): {snippet}...")

# 4. Uploads
print("\n--- [TABLE: uploads] ---")
uploads = cursor.execute("SELECT id, filename, file_type, storage_provider FROM uploads ORDER BY created_at DESC LIMIT 5").fetchall()
if not uploads:
    print("No uploads found.")
else:
    for up in uploads:
        print(f"File: {up['filename']} | Type: {up['file_type']} | Storage: {up['storage_provider']}")

print("\n" + "=" * 60)
print("DATABASE STATUS: Active SQLite Database Connected Successfully!")
print("=" * 60)
conn.close()
