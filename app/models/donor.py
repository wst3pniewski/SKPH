from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.donation import DonationItem, DonationMoney


class Donor(db.Model):
    donor_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(20), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    donations_money: Mapped[List["DonationMoney"]] = relationship(
        back_populates="donor",
        cascade="all, delete-orphan"
    )
    donations_items: Mapped[List["DonationItem"]] = relationship(
        back_populates="donor",
        cascade="all, delete-orphan"
    )

    def request_confirmation(self, donation_id: int) -> str:
        """Request confirmation for a specific donation."""
        return f"Confirmation requested for donation ID: {donation_id}"

    def __repr__(self):
        return f"<Donor(donor_id={self.donor_id!r}, name={self.first_name!r}, \
                last_name={self.last_name!r}, phone_number={self.phone_number!r}, \
                email={self.email!r}, donations_money={self.donations_money!r}, \
                donations_items={self.donations_items!r})>"
