#!/usr/bin/env python3
from services.api.app import db

def print_table_info(conn, table):
    cur = conn.cursor()
    try:
        cur.execute(f"PRAGMA table_info({table})")
        rows = cur.fetchall()
        print(f"Table {table} columns:")
        for r in rows:
            print('  ', r)
    except Exception as e:
        print(f"Could not read {table}: {e}")

if __name__ == '__main__':
    conn = db.connect()
    for t in ('mission_target', 'recruiter_strength', 'market_capacity'):
        print_table_info(conn, t)
    print('\nRunning migrations...')
    db._migrate_mission_feasibility_schema(conn)
    print('\nAfter migration:')
    for t in ('mission_target', 'recruiter_strength', 'market_capacity'):
        print_table_info(conn, t)
    conn.close()
