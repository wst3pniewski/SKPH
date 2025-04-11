from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Address(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    street: Mapped[str] = mapped_column(db.String, nullable=False)
    street_number: Mapped[str] = mapped_column(db.String, nullable=False)
    city: Mapped[str] = mapped_column(db.String, nullable=False)
    voivodeship: Mapped[str] = mapped_column(db.String, nullable=False)

    def __repr__(self):
        return (f'<Address(id={self.id!r}, street={self.street!r}, \
                street_number={self.street_number!r}, city={self.city!r}, \
                voivodeship={self.voivodeship!r})>')
