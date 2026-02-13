import sqlite3
import os
import pandas as pd

from backend.ingestion.loaders.market_share_loader import load_market_share
from backend.routers.imports import ensure_fact_tables


def test_market_loader_basic(tmp_path):
    csv = tmp_path / "market.csv"
    csv.write_text("FY,RQ,SERVICE,SUM OF CONTRACTS,ZIP,STATION\n2024,Q1,Logistics,1234,27587,3J3H - WAKE FOREST\n")

    con = sqlite3.connect(":memory:")
    # ensure the fact table exists
    ensure_fact_tables(con)

    batch_id = "test_batch_market"
    load_market_share(con, str(csv), batch_id)

    cur = con.cursor()
    cur.execute("SELECT fy, per, mkt, rsid, zip, contracts, share FROM fact_market_share_contracts WHERE batch_id=?", (batch_id,))
    rows = cur.fetchall()
    assert len(rows) == 1
    fy, per, mkt, rsid, zipv, contracts, share = rows[0]
    assert fy == 2024
    assert per in ("Q1", "q1", "QTR1", "1")
    assert mkt == "Logistics"
    assert rsid == "3J3H"
    assert zipv == "27587"
    assert contracts == 1234.0
