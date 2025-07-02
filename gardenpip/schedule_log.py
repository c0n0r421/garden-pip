import json
import os
from typing import Any, Dict, List

from .shelf_logic import get_session
from .db_models import Tray


def log_schedule(entry: Dict[str, Any], base_dir: str) -> None:
    """Append a schedule entry to the log file inside ``base_dir``."""
    # fill tray info from database if missing
    if 'tray_id' not in entry:
        session = get_session()
        tray = session.query(Tray).first()
        if tray:
            entry['tray_id'] = tray.id
            entry.setdefault('shelf_id', tray.shelf_id)
        session.close()

    os.makedirs(base_dir, exist_ok=True)
    log_path = os.path.join(base_dir, "schedule_log.json")

    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    else:
        data = []

    data.append(entry)
    with open(log_path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2)
