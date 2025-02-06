from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Coordinates(db.Model):
    __tablename__ = 'coordinates'

    id: Mapped[int] = mapped_column(primary_key=True)
    x: Mapped[float] = mapped_column(nullable=False)
    y: Mapped[float] = mapped_column(nullable=False)

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"<Coordinates(id={self.id!r}, x={self.x!r}, y={self.y!r})"


class POI(db.Model):
    __tablename__ = 'poi'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    coordinates_id: Mapped[int] = mapped_column(ForeignKey('coordinates.id'))
    coordinates: Mapped[Coordinates] = relationship(backref='poi')
    status: Mapped[bool] = mapped_column(default=True, nullable=False)
    type_of_poi: Mapped[str] = mapped_column(nullable=False)

    def __init__(self, name: str, coordinates: Coordinates,
                 type_of_poi: str, status: bool = True):
        self.name = name
        self.coordinates = coordinates
        self.type_of_poi = type_of_poi
        self.status = status

    def __repr__(self):
        return f"<POI(id={self.id!r} ,name={self.name!r}, coordinates={self.coordinates!r}, \
                type_of_poi={self.type_of_poi!r}, status={self.status!r})>"


class DangerArea(db.Model):
    __tablename__ = 'danger_area'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[bool] = mapped_column(default=True)
    coordinates: Mapped[str] = mapped_column(JSON, nullable=False)

    def __init__(self, name: str, coordinates: list, status: bool = True):
        self.name = name
        self.coordinates = coordinates
        self.status = status

    def __repr__(self):
        return f"<DangerArea(id={self.id!r}, name={self.name!r}, status={self.status}, \
                coordinates={self.coordinates!r})>"


class ReliefArea(db.Model):
    __tablename__ = 'relief_area'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[bool] = mapped_column(default=True, nullable=False)
    coordinates: Mapped[str] = mapped_column(JSON, nullable=False)

    def __init__(self, name: str, coordinates: list, status: bool = True):
        self.name = name
        self.coordinates = coordinates
        self.status = status

    def __repr__(self):
        return f"<ReliefArea(id={self.id} ,name={self.name}, status={self.status}, \
                coordinates={self.coordinates!r})>"
