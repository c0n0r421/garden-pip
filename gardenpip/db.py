from __future__ import annotations

import datetime as _dt
from typing import Iterable, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class ShelfSystem(Base):
    __tablename__ = "shelf_systems"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    shelves: Mapped[list["Shelf"]] = relationship(back_populates="system", cascade="all, delete-orphan")


class Shelf(Base):
    __tablename__ = "shelves"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String)
    system_id: Mapped[int] = mapped_column(ForeignKey("shelf_systems.id"))

    system: Mapped["ShelfSystem"] = relationship(back_populates="shelves")
    trays: Mapped[list["Tray"]] = relationship(back_populates="shelf", cascade="all, delete-orphan")


class Tray(Base):
    __tablename__ = "trays"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String)
    shelf_id: Mapped[int] = mapped_column(ForeignKey("shelves.id"))

    shelf: Mapped["Shelf"] = relationship(back_populates="trays")
    logs: Mapped[list["NutrientLog"]] = relationship(back_populates="tray", cascade="all, delete-orphan")


class NutrientLog(Base):
    __tablename__ = "nutrient_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    tray_id: Mapped[int] = mapped_column(ForeignKey("trays.id"))
    date: Mapped[_dt.datetime] = mapped_column(DateTime, default=_dt.datetime.utcnow)
    ph: Mapped[float] = mapped_column(Float)
    ppm: Mapped[float] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(String, default="")

    tray: Mapped["Tray"] = relationship(back_populates="logs")


def get_session(db_path: str) -> Session:
    """Return a SQLAlchemy :class:`Session` for the given SQLite path."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


# ── CRUD helper functions ─────────────────────────────────────────────────────

def add_nutrient_log(session: Session, tray_id: int, date: Optional[_dt.datetime] = None,
                     ph: float = 0.0, ppm: float = 0.0, notes: str = "") -> NutrientLog:
    log = NutrientLog(tray_id=tray_id, date=date or _dt.datetime.utcnow(), ph=ph, ppm=ppm, notes=notes)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def update_nutrient_log(session: Session, log_id: int, **kwargs) -> Optional[NutrientLog]:
    log = session.get(NutrientLog, log_id)
    if not log:
        return None
    for key, val in kwargs.items():
        if hasattr(log, key):
            setattr(log, key, val)
    session.commit()
    session.refresh(log)
    return log


def delete_nutrient_log(session: Session, log_id: int) -> bool:
    log = session.get(NutrientLog, log_id)
    if not log:
        return False
    session.delete(log)
    session.commit()
    return True


def search_nutrient_logs(session: Session, text: str | None = None, tray_id: int | None = None) -> Iterable[NutrientLog]:
    query = session.query(NutrientLog)
    if text:
        pattern = f"%{text}%"
        query = query.filter(NutrientLog.notes.ilike(pattern))
    if tray_id is not None:
        query = query.filter(NutrientLog.tray_id == tray_id)
    return query.order_by(NutrientLog.date.desc()).all()
