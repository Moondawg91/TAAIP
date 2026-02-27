#!/usr/bin/env python3
"""Seed RBAC roles, permissions, and an initial admin user.

Run: python3 services/api/seed_rbac.py
"""
import os
import sys
from services.api.app import db

def seed():
    conn = db.connect()
    cur = conn.cursor()
    now = __import__('datetime').datetime.utcnow().isoformat()
    try:
        # Ensure core role_template rows exist
        roles = [
            ('ADMIN','Administrator','Full system administrator'),
            ('420T_FULL','420T Full','Full 420T non-admin access (exports + uploads)'),
            ('COMMAND_READONLY','Command Readonly','Command-level readonly (view + export)'),
            ('STAFF_PLANNER','Staff Planner','Planning and Events editors'),
            ('STAFF_ANALYST','Staff Analyst','Analytics focused'),
            ('USER','User','Baseline user')
        ]
        for k,n,d in roles:
            cur.execute('INSERT OR IGNORE INTO role_template(key,name,description) VALUES (?,?,?)', (k,n,d))

        # Ensure an admin user
        admin_user = os.getenv('RBAC_ADMIN_USER', 'admin@example.com')
        cur.execute('INSERT OR IGNORE INTO users(username, display_name, email, created_at, record_status) VALUES (?,?,?,?,?)', (admin_user, 'Admin', admin_user, now, 'active'))
        conn.commit()
        cur.execute('SELECT id FROM users WHERE username=?', (admin_user,))
        row = cur.fetchone()
        if row:
            uid = row[0]
            # assign ADMIN role template
            cur.execute('INSERT OR IGNORE INTO user_role_template(user_id, role_key, assigned_at) VALUES (?,?,?)', (uid, 'ADMIN', now))
            conn.commit()
        print('RBAC seed completed')
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    seed()
