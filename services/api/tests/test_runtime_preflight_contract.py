from services.api.app.runtime_env import runtime_preflight


def test_runtime_preflight_includes_release_contract_checks(tmp_path, monkeypatch):
    monkeypatch.setenv('TAAIP_DB_PATH', str(tmp_path / 'release.db'))
    monkeypatch.setenv('TAAIP_UPLOAD_DIR', str(tmp_path / 'imports'))
    monkeypatch.setenv('TAAIP_REFRESH_UPLOAD_DIR', str(tmp_path / 'refresh'))
    monkeypatch.setenv('EXPORT_STORAGE_DIR', str(tmp_path / 'exports'))
    monkeypatch.setenv('TAAIP_DOCUMENTS_PATH', str(tmp_path / 'documents'))

    report = runtime_preflight()

    assert report['status'] == 'ok'
    names = {item['name'] for item in report['checks']}
    assert 'db_directory' in names
    assert 'taaip_upload_dir' in names
    assert 'taaip_refresh_upload_dir' in names
    assert 'export_storage_dir' in names
    assert 'taaip_documents_path' in names
    assert 'database_url' in names
