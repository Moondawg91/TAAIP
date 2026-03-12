# Archive staging runs (fact_enlistments_bn)

This document describes the `scripts/archive_staging.py` helper that archives staging rows
from `fact_enlistments_bn` to CSV and optionally deletes them from the local SQLite DB.

Key points
- The script is intentionally conservative: run it with `--dry-run` first to see candidates.
- By default it archives runs that are either committed in `fact_enlistments` or older than
  `--retention-days` (default 30).
- The script writes CSV files to `data/archive/` and deletes exported rows only when not
  running with `--dry-run`.

Usage

Dry-run (safe; does not delete or VACUUM):

```sh
python3 scripts/archive_staging.py --dry-run
```

Archive candidates and delete staging rows (will VACUUM):

```sh
python3 scripts/archive_staging.py
```

Archive a specific run:

```sh
python3 scripts/archive_staging.py --commit-run run_20260306_041436_65d47a
```

Makefile

You can also run via `make archive-staging` which calls the script in the workspace.

Scheduling (examples)

- Cron (run nightly at 02:30):

```cron
30 2 * * * cd /path/to/TAAIP && /usr/bin/python3 scripts/archive_staging.py
```

- macOS launchd (run daily at 03:00): create a plist like `~/Library/LaunchAgents/com.taaip.archive.plist` with the program arguments set to run the script. Example plist snippet:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.taaip.archive</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/full/path/to/TAAIP/scripts/archive_staging.py</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>3</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
</dict>
</plist>
```

Notes and safety
- The script expects access to the local SQLite file `data/taaip.sqlite3` (configurable via `--db-path` or `TAAIP_DB_PATH`).
- Don't run the destructive mode while the API is actively writing to the DB; stop the API or ensure no concurrent writes.
- Use `--dry-run` first to confirm candidates.

If you want, I can add a CI job or a deployment step to install a launchd plist on the server — tell me where you'd like it scheduled.
