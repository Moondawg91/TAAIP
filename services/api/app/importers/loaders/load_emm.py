def load_emm(df, ctx, conn):
    """Basic EMM loader stub: attempts to insert rows into `fact_emm_events` if table exists.
    Returns number of rows inserted (best-effort)."""
    cur = conn.cursor()
    # quick check if table exists
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fact_emm_events'")
        if not cur.fetchone():
            return 0
    except Exception:
        return 0

    inserted = 0
    # naive insert: try to guess columns present
    cols = []
    try:
        cols = list(df.columns)
    except Exception:
        return 0

    # Map dataframe columns to a simple insert into fact_emm_events
    # This loader is a stub: it will insert JSON payload into a generic `payload` column
    # if such a column exists; otherwise it will attempt to insert nothing.
    try:
        cur.execute("PRAGMA table_info(fact_emm_events)")
        table_cols = [r[1] for r in cur.fetchall()]
        if 'payload' in table_cols:
            for _, row in df.iterrows():
                payload = row.to_json()
                cur.execute('INSERT INTO fact_emm_events (payload) VALUES (?)', (payload,))
                inserted += 1
            conn.commit()
        else:
            # fallback: no payload column, skip inserting
            inserted = 0
    except Exception:
        return 0

    return inserted
