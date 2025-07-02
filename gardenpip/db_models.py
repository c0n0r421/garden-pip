import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

DB_PATH = os.path.join(os.path.dirname(__file__), 'garden.db')
engine = create_engine(f'sqlite:///{DB_PATH}')
SessionLocal = sessionmaker(bind=engine)

class ShelfSystem(Base):
    __tablename__ = 'shelf_systems'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    shelves = relationship('Shelf', back_populates='system')

class Shelf(Base):
    __tablename__ = 'shelves'
    id = Column(Integer, primary_key=True)
    system_id = Column(Integer, ForeignKey('shelf_systems.id'))
    name = Column(String)
    trays = relationship('Tray', back_populates='shelf')
    system = relationship('ShelfSystem', back_populates='shelves')

class Tray(Base):
    __tablename__ = 'trays'
    id = Column(Integer, primary_key=True)
    shelf_id = Column(Integer, ForeignKey('shelves.id'))
    label = Column(String)
    shelf = relationship('Shelf', back_populates='trays')

def init_db():
    """Create database tables if they don't exist."""
    Base.metadata.create_all(engine)
