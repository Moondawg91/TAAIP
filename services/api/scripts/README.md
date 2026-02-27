# Org unit importer

Run the importer (dry-run):

```bash
.venv/bin/python services/api/scripts/import_org_units.py --csv /path/to/usarec_units.csv --dry-run
```

To execute and write to DB:

```bash
.venv/bin/python services/api/scripts/import_org_units.py --csv /path/to/usarec_units.csv
```

Options:
- `--source` set an import source tag (default `usarec_master`)
- `--truncate` remove existing rows from the same source before importing
