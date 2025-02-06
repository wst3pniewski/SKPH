from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

from .charity_campaign import volunteer_campaign_association

if TYPE_CHECKING:
    from .charity_campaign import OrganizationCharityCampaign
    from .task import Task


class Volunteer(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(20), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    address = relationship('Address')
    address_id = mapped_column(ForeignKey('address.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    tasks: Mapped[List["Task"]] = relationship(back_populates='volunteer')
    campaigns: Mapped[List["OrganizationCharityCampaign"]] = (
        relationship(secondary=volunteer_campaign_association,
                     back_populates='volunteers')
    )

    def __repr__(self):
        return f'<Volunteer:(id={self.id!r}, first_name={self.first_name!r}, \
                 last_name={self.last_name!r}, email={self.email!r}, \
                 phone={self.phone!r}, address_id={self.address_id!r})>'
