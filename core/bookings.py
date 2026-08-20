import csv
from pathlib import Path
from datetime import datetime


def save_booking(client_id: str, booking: dict):
    """Append a booking to a per-client CSV file"""
    bookings_dir = Path(f"clients/{client_id}")
    bookings_dir.mkdir(parents=True, exist_ok=True)
    file_path = bookings_dir / "bookings.csv"

    file_exists = file_path.exists()

    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "name", "phone", "service", "preferred_date", "preferred_time", "notes"])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            booking.get("name", ""),
            booking.get("phone", ""),
            booking.get("service", ""),
            booking.get("preferred_date", ""),
            booking.get("preferred_time", ""),
            booking.get("notes", ""),
        ])