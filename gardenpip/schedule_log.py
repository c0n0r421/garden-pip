import json
import os


def log_schedule(entry, base_dir):
    """Append a schedule entry to base_dir/schedule_log.json."""
    os.makedirs(base_dir, exist_ok=True)
    log_path = os.path.join(base_dir, 'schedule_log.json')
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError):
            data = []
    else:
        data = []
    data.append(entry)
    with open(log_path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2)
    return log_path
