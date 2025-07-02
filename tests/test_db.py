import os
from gardenpip.db import (
    ShelfSystem,
    Shelf,
    Tray,
    add_nutrient_log,
    delete_nutrient_log,
    get_session,
    search_nutrient_logs,
    update_nutrient_log,
)


def test_crud_nutrient_log(tmp_path):
    db_path = tmp_path / "test.db"
    session = get_session(str(db_path))

    system = ShelfSystem(name="Sys")
    shelf = Shelf(label="S1", system=system)
    tray = Tray(label="T1", shelf=shelf)
    session.add(system)
    session.commit()

    log = add_nutrient_log(session, tray.id, ph=6.5, ppm=950, notes="first")
    assert log.id is not None

    logs = search_nutrient_logs(session, "first")
    assert len(logs) == 1

    updated = update_nutrient_log(session, log.id, notes="updated")
    assert updated and updated.notes == "updated"

    assert delete_nutrient_log(session, log.id)
    assert search_nutrient_logs(session) == []
