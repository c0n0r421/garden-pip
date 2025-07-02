import json
import os
from gardenpip.schedule_log import log_schedule


def test_log_written_when_base_dir_missing(tmp_path):
    base = tmp_path / 'data_dir'
    entry = {
        'date': '2024-01-01',
        'manufacturer': 'M',
        'series': 'S',
        'stage': 'Stage',
        'plant_category': 'Cat',
        'unit': 'metric',
        'volume': 1,
        'cal_mag': None,
        'lines': ['line'],
    }

    log_schedule(entry, str(base))

    log_file = base / 'schedule_log.json'
    assert log_file.exists()
    with open(log_file, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    assert entry in data
