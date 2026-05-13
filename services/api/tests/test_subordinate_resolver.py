from typing import List

import pytest
from sqlalchemy import text

from database import rsid_hierarchy
from services.api.app import database
from services.api.app.services.org_unit_resolver import resolve_subordinate_units
from services.api.scripts.import_org_units import connect_db, ensure_indexes, link_parents, upsert_rows
from services.api.scripts.seed_master_org_units import ensure_org_unit_table


def _seed_canonical_org_units(db_path: str) -> None:
    conn = connect_db(db_path)
    try:
        ensure_org_unit_table(conn)
        ensure_indexes(conn)
        rows = rsid_hierarchy.get_org_unit_seed_rows()
        upsert_rows(conn, rows, "test_seed", dry_run=False)
        link_parents(conn, dry_run=False)
    finally:
        conn.close()


def _expected_descendants(unit_rsid: str) -> List[str]:
    with database.engine.connect() as conn:
        root = conn.execute(
            text(
                """
                SELECT id, rsid, echelon
                FROM org_unit
                WHERE rsid = :rsid OR upper(rsid) = upper(:rsid)
                LIMIT 1
                """
            ),
            {"rsid": unit_rsid},
        ).mappings().first()
        assert root is not None

        if str(root.get("echelon") or "").upper() == "STN":
            return [root["rsid"]]

        rows = conn.execute(
            text(
                """
                WITH RECURSIVE descendants AS (
                    SELECT id, rsid, 0 AS depth
                    FROM org_unit
                    WHERE id = :root_id
                    UNION ALL
                    SELECT child.id, child.rsid, descendants.depth + 1
                    FROM org_unit AS child
                    JOIN descendants ON child.parent_id = descendants.id
                    WHERE COALESCE(child.record_status, 'active') != 'deleted'
                )
                SELECT DISTINCT rsid
                FROM descendants
                WHERE depth > 0 AND rsid IS NOT NULL
                ORDER BY rsid ASC
                """
            ),
            {"root_id": root["id"]},
        ).mappings().all()
        return [row["rsid"] for row in rows]


@pytest.fixture()
def seeded_resolver_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "resolver.sqlite3")
    monkeypatch.setenv("TAAIP_DB_PATH", db_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    database.reload_engine_if_needed()
    _seed_canonical_org_units(db_path)
    database.reload_engine_if_needed()
    return db_path


@pytest.mark.parametrize(
    "unit_rsid, expected_echelon",
    [
        ("USAREC", "CMD"),
        ("1ST BDE", "BDE"),
        ("1A", "BN"),
        ("1A1", "CO"),
        ("1A1D", "STN"),
    ],
)
def test_resolver_returns_flat_sorted_subordinates(seeded_resolver_db, unit_rsid, expected_echelon):
    resolved = resolve_subordinate_units(unit_rsid)
    expected = _expected_descendants(unit_rsid)

    assert resolved == expected
    assert resolved == sorted(resolved)
    assert len(resolved) == len(set(resolved))

    with database.engine.connect() as conn:
        all_rsids = {
            row["rsid"]
            for row in conn.execute(text("SELECT rsid FROM org_unit WHERE rsid IS NOT NULL")).mappings().all()
        }
    assert set(resolved).issubset(all_rsids)

    if expected_echelon == "STN":
        assert resolved == [unit_rsid]
    else:
        assert unit_rsid not in resolved


def test_resolver_returns_all_subordinates_for_command(seeded_resolver_db):
    resolved = resolve_subordinate_units("USAREC")

    with database.engine.connect() as conn:
        total_units = conn.execute(text("SELECT COUNT(1) AS cnt FROM org_unit")).mappings().first()["cnt"]

    assert len(resolved) == total_units - 1
    assert resolved == _expected_descendants("USAREC")
    assert "1ST BDE" in resolved
    assert "1A1D" in resolved