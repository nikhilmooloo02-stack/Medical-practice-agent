import csv
from pathlib import Path
from core.timezone_utils import now_sa
import uuid


def get_or_create_session_id(session_state) -> str:
    """Give each browser session a unique ID so we can group its messages together"""
    if "conversation_id" not in session_state or session_state.conversation_id is None:
        session_state.conversation_id = str(uuid.uuid4())[:8]
    return session_state.conversation_id


def log_message(client_id: str, conversation_id: str, role: str, content: str):
    """Append one message to the client's conversation log CSV"""
    log_dir = Path(f"clients/{client_id}")
    log_dir.mkdir(parents=True, exist_ok=True)
    file_path = log_dir / "conversation_log.csv"

    file_exists = file_path.exists()

    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "conversation_id", "role", "message"])
        writer.writerow([
            now_sa().isoformat(timespec="seconds"),
            conversation_id,
            role,
            content,
        ])