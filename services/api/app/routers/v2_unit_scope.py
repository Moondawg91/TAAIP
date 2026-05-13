from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from .. import database
from ..services.org_unit_resolver import resolve_subordinate_units
from .rbac import require_perm


router = APIRouter(prefix="/v2/unit-scope", tags=["v2_unit_scope"])


@router.get("/subordinates")
def get_subordinates(rsid: str, user: dict = Depends(require_perm("dashboards.view"))):
    target = (rsid or "").strip()
    if not target:
        raise HTTPException(status_code=400, detail="rsid is required")

    database.reload_engine_if_needed()
    with database.engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT rsid, echelon, COALESCE(display_name, name, rsid) AS display_name
                FROM org_unit
                WHERE rsid = :rsid OR upper(rsid) = upper(:rsid)
                LIMIT 1
                """
            ),
            {"rsid": target},
        ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Org unit not found")

    subordinates = resolve_subordinate_units(row["rsid"])
    return {
        "rsid": row["rsid"],
        "echelon": row.get("echelon"),
        "display_name": row.get("display_name"),
        "subordinates": subordinates,
        "count": len(subordinates),
    }
