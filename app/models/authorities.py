from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from .address import Address


class Authorities(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    approved: Mapped[bool] = mapped_column(default=False)
    address: Mapped["Address"] = relationship()
    address_id: Mapped[int] = mapped_column(ForeignKey('address.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    def __repr__(self):
        return f'<Authorities(id={self.id!r} name={self.name!r}, \
                phone={self.phone!r}, approved={self.approved!r}, \
                address={self.address!r})>'

    def get_approve_status(self):
        return self.approved

    def approve(self):
        self.approved = True
        db.session.commit()

    def disapprove(self):
        self.approved = False
        db.session.commit()
