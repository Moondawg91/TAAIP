from services.api.app import database
from services.api.app.services import decision_writeback


def _db():
    return next(database.get_db())


def test_writeback_persists_decision_and_audit():
    db = _db()
    out = decision_writeback.writeback_change(
        db,
        actor="tester",
        scope_type="CO",
        scope_value="E12",
        decision_type="targeting_shift",
        summary="Shift focus",
        before_json={"zip": "11111"},
        after_json={"zip": "22222"},
    )
    assert out["status"] == "ok"
    assert out["decision_id"]
    assert out["audit_id"]
