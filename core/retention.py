import csv
from pathlib import Path
from datetime import timedelta, datetime
from core.timezone_utils import now_sa


def clean_old_records(client_id: str, config: dict):
    """Delete conversation log and booking rows older than the configured retention period"""
    retention_days = config["compliance"]["data_retention_days"]
    cutoff = now_sa() - timedelta(days=retention_days)

    _clean_csv(Path(f"clients/{client_id}/conversation_log.csv"), cutoff, timestamp_col="timestamp")
    _clean_csv(Path(f"clients/{client_id}/bookings.csv"), cutoff, timestamp_col="timestamp")


def _clean_csv(file_path: Path, cutoff: datetime, timestamp_col: str):
    if not file_path.exists():
        return

    with open(file_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not rows or not fieldnames:
        return

    kept_rows = []
    for row in rows:
        try:
            row_time = datetime.fromisoformat(row[timestamp_col])
            if row_time.tzinfo is None:
                # Handle old rows saved before timezone-awareness was added
                kept_rows.append(row)
                continue
            if row_time >= cutoff:
                kept_rows.append(row)
        except (KeyError, ValueError):
            kept_rows.append(row)

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept_rows)