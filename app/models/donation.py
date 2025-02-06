from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.donor import Donor

if TYPE_CHECKING:
    from .charity_campaign import OrganizationCharityCampaign


class DonationType(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)


class DonationMoney(db.Model):
    donationMoney_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(Text)
    donation_date: Mapped[date] = date.today()
    donation_type_id: Mapped[int] = mapped_column(ForeignKey('donation_type.id'))
    donation_type: Mapped["DonationType"] = relationship()
    cashAmount: Mapped[float] = mapped_column(nullable=False)
    charity_campaign_id: Mapped[int] = mapped_column(ForeignKey('organization_charity_campaign.id'))
    charity_campaign: Mapped["OrganizationCharityCampaign"] = relationship()
    donor_id: Mapped[int] = mapped_column(ForeignKey('donor.donor_id'))
    donor: Mapped["Donor"] = relationship(back_populates="donations_money")

    def return_confirmation(self) -> str:
        return f"Donation confirmed: id: {self.donationMoney_id}, {self.description}, Amount: {self.cashAmount}"

    def __repr__(self):
        return f"<Donation(description={self.description}, amount={self.cashAmount})>"


class DonationItem(db.Model):
    donationItem_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(Text)
    donation_date: Mapped[date] = date.today()
    donation_type_id: Mapped[int] = mapped_column(ForeignKey('donation_type.id'))
    amount: Mapped[float] = mapped_column(nullable=False)
    donor_id: Mapped[int] = mapped_column(ForeignKey('donor.donor_id'))
    donor: Mapped["Donor"] = relationship(back_populates="donations_items")
    charity_campaign_id: Mapped[int] = mapped_column(ForeignKey('organization_charity_campaign.id'))
    charity_campaign: Mapped["OrganizationCharityCampaign"] = relationship()
    donation_type: Mapped["DonationType"] = relationship()

    def return_confirmation(self) -> str:
        return f"Donation confirmed: id: {self.donationItem_id}, {self.description}, Number: {self.amount}"

    def __repr__(self):
        return f"<Donation(description={self.description}, amount={self.amount})>"
