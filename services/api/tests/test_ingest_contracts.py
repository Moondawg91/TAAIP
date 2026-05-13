from services.api.app.services import ingest_contracts


def test_ingest_contract_validation_market_ok():
    ok, data = ingest_contracts.validate_contract(
        "market",
        ["station_rsid", "zip_code", "market_category", "qma_population"],
    )
    assert ok is True
    assert data["valid"] is True


def test_ingest_contract_validation_invalid_schema():
    ok, data = ingest_contracts.validate_contract("execution_quality", ["lead_key", "station_rsid"])
    assert ok is False
    assert data["missing_required"]
