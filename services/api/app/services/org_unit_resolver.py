from typing import List

from sqlalchemy import text

from services.api.app import database


def resolve_subordinate_units(unit_rsid: str) -> List[str]:
    target = (unit_rsid or "").strip()
    if not target:
        return []

    database.reload_engine_if_needed()
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
            {"rsid": target},
        ).mappings().first()
        if not root:
            return []

        echelon = str(root.get("echelon") or "").upper()
        if echelon == "STN":
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