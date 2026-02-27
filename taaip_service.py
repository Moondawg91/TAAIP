"""Tiny shim: expose operational `app` and `init_db` from services.api.app.

Tests expect `from taaip_service import app, init_db`. Keep this module
minimal and delegated to the canonical implementation under
`services.api.app`.
"""
from services.api.app.main import app  # type: ignore
from services.api.app.db import init_schema as _init_schema, init_db as _legacy_init_db, get_db_conn  # type: ignore
import os
import pathlib


def _ensure_root_unit(conn):
	"""Ensure a USAREC-like root exists in `org_unit` so selection/default works."""
	try:
		cur = conn.cursor()
		try:
			# Preferred schema with display_name/echelon
			cur.execute("SELECT rsid FROM org_unit WHERE rsid = 'USAREC' LIMIT 1")
			if cur.fetchone():
				return
			cur.execute(
				"INSERT INTO org_unit(rsid, display_name, echelon, parent_rsid, name, type, created_at, updated_at) VALUES (?,?,?,?,?,?,datetime('now'),datetime('now'))",
				('USAREC', 'USAREC', 'CMD', None, 'USAREC', 'CMD'),
			)
			conn.commit()
			return
		except Exception:
			# Fallback to legacy schema columns
			try:
				cur.execute("SELECT rsid FROM org_unit WHERE rsid = 'USAREC' LIMIT 1")
				if cur.fetchone():
					return
				cur.execute(
					"INSERT INTO org_unit(name, type, parent_id, rsid, created_at, updated_at) VALUES (?,?,?,?,datetime('now'),datetime('now'))",
					('USAREC', 'CMD', None, 'USAREC'),
				)
				conn.commit()
			except Exception:
				pass
	except Exception:
		pass


def init_db():
	"""Initialize the operational schema in the test-friendly path.

	Tests expect the DB at `./data/taaip.sqlite3`. Ensure the directory
	exists, set `TAAIP_DB_PATH` for the operational DB module, then call
	the canonical `init_schema` implementation.
	"""
	db_path = os.path.join(os.getcwd(), "data", "taaip.sqlite3")
	pathlib.Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
	os.environ["TAAIP_DB_PATH"] = db_path

	# Run both schema initializers: the operational `init_schema` (new)
	# and the legacy `init_db` (compat) so both singular/plural table
	# names are present for the tests and older endpoints.
	try:
		_init_schema()
	except Exception:
		pass
	try:
		_legacy_init_db()
	except Exception:
		pass

	# Ensure SQLAlchemy engine used by `services.api.app` points at the
	# test DB path we just configured so SQLAlchemy-backed endpoints
	# observe changes made via direct sqlite connections in tests.
	try:
		from services.api.app import database as _database
		try:
			# update DATABASE_URL env to match TAAIP_DB_PATH and reload engine
			os.environ["DATABASE_URL"] = f"sqlite:///{os.environ.get('TAAIP_DB_PATH')}"
			_database.reload_engine_if_needed()
		except Exception:
			pass
	except Exception:
		pass

	# Ensure a root org_unit exists so v2 selection endpoints return a root
	try:
		conn = get_db_conn()
		try:
			_ensure_root_unit(conn)
		finally:
			try:
				conn.close()
			except Exception:
				pass
	except Exception:
		pass


__all__ = ["app", "init_db", "get_db_conn"]
