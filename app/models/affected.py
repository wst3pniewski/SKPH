from typing import TYPE_CHECKING, List
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from .address import Address
    from .request import Request


class Affected(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(20), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    needs: Mapped[str] = mapped_column(Text)
    address: Mapped["Address"] = relationship()
    address_id: Mapped[int] = mapped_column(ForeignKey('address.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    requests: Mapped[List["Request"]] = relationship(back_populates='affected',
                                                     cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Affected(id={self.id!r}, first_name={self.first_name!r},\
                last_name={self.last_name!r} needs={self.needs!r}, \
                address={self.address!r}, requests={self.requests!r})>'
