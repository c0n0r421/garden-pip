import json
import os
from typing import Any, List


def load_shelves(path: str) -> List[Any]:
    """Load shelf data from JSON file."""
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def save_shelves(path: str, data: List[Any]) -> None:
    """Save shelf data to JSON file."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2)

from .db_models import SessionLocal, ShelfSystem, Shelf, Tray, init_db

init_db()


def get_session():
    """Return a new SQLAlchemy session."""
    return SessionLocal()


def get_system_layout(system_name: str = 'default') -> List[dict]:
    """Return shelf layout for the given system."""
    session = get_session()
    system = session.query(ShelfSystem).filter_by(name=system_name).first()
    layout: List[dict] = []
    if system:
        for shelf in system.shelves:
            layout.append(
                {
                    'id': shelf.id,
                    'name': shelf.name,
                    'trays': [{'id': t.id, 'label': t.label} for t in shelf.trays],
                }
            )
    session.close()
    return layout


def save_system_layout(system_name: str, data: List[dict]) -> None:
    """Save layout data for the given system."""
    session = get_session()
    system = session.query(ShelfSystem).filter_by(name=system_name).first()
    if not system:
        system = ShelfSystem(name=system_name)
        session.add(system)
        session.commit()
    # clear existing shelves and trays
    for shelf in list(system.shelves):
        session.query(Tray).filter_by(shelf_id=shelf.id).delete()
        session.delete(shelf)
    session.commit()
    # add new shelves
    for shelf_data in data:
        shelf = Shelf(name=shelf_data.get('name', ''), system_id=system.id)
        session.add(shelf)
        session.flush()
        for tray_data in shelf_data.get('trays', []):
            tray = Tray(label=tray_data.get('label', ''), shelf_id=shelf.id)
            session.add(tray)
    session.commit()
    session.close()
