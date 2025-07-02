import os
from gardenpip.config_logic import load_configs, save_configs

def test_save_and_load_configs(tmp_path):
    cfg_path = tmp_path / 'cfg.json'
    data = {'default': {'foo': 1}}
    save_configs(str(cfg_path), data)
    loaded = load_configs(str(cfg_path))
    assert loaded == data
