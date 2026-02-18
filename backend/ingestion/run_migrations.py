"""
Run SQL migration files in backend/migrations in lexical order.

Usage (on droplet):
  sudo docker compose exec -T backend python /app/backend/ingestion/run_migrations.py
"""
import os
import sqlite3
import glob

DB = os.getenv('DB_PATH', '/app/recruiting.db')
MIG_GLOB = '/app/backend/migrations/*.sql'

def main():
    files = sorted(glob.glob(MIG_GLOB))
    if not files:
        print('No migration files found at', MIG_GLOB)
        return
    print('DB:', DB)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    for f in files:
        print('Applying', f)
        with open(f, 'r') as fh:
            sql = fh.read()
            cur.executescript(sql)
            con.commit()
    con.close()
    print('Migrations applied:', len(files))

if __name__ == '__main__':
    main()
