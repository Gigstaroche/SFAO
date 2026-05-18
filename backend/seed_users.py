#!/usr/bin/env python3
import hashlib
from database import init_db, insert_user, get_user_by_email, get_connection

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def seed():
    init_db()
    users = [
        ("Administrator", "admin@sfao.local", "AdminPass123!", "admin"),
        ("Dev Admin", "dev@sfao.local", "DevPass123!", "dev_admin"),
        ("Employee User", "employee@sfao.local", "EmployeePass123!", "employee"),
        ("Analyst User", "analyst@sfao.local", "AnalystPass123!", "analyst"),
    ]

    created = []
    for name, email, pw, role in users:
        existing = get_user_by_email(email)
        if existing:
            # If the user exists but role differs, update to requested role
            if existing.get('role') != role:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("UPDATE users SET role = ? WHERE email = ?", (role, email))
                conn.commit()
                conn.close()
                created.append((email, 'updated-role'))
            else:
                created.append((email, 'exists'))
            continue
        h = hash_password(pw)
        row_id = insert_user(name, email, h, role)
        created.append((email, row_id))

    print("Seed complete. Results:")
    for (email, status) in created:
        print(f" - {email}: {status}")

    print('\nCredentials (use these to login via the UI):')
    print(' - Admin: admin@sfao.local / AdminPass123! (role: admin)')
    print(' - Dev Admin: dev@sfao.local / DevPass123! (role: dev_admin)')
    print(' - Employee: employee@sfao.local / EmployeePass123! (role: employee)')
    print(' - Analyst: analyst@sfao.local / AnalystPass123! (role: analyst)')

if __name__ == '__main__':
    seed()
