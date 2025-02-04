from datetime import date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.donor import Donor


class DonationMoney(db.Model):
    donationMoney_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]
    donation_date: Mapped[date] = date.today()
    donation_type_id: Mapped[int] = mapped_column(ForeignKey('donation_type.id'))
    donation_type = relationship('DonationType')
    cashAmount: Mapped[float]
    charity_campaign_id: Mapped[int] = mapped_column(ForeignKey('organization_charity_campaign.id'))
    charity_campaign = relationship('OrganizationCharityCampaign')
    donor_id: Mapped[int] = mapped_column(ForeignKey('donor.donor_id'))
    donor: Mapped["Donor"] = relationship(back_populates="donations_money")

    def return_confirmation(self) -> str:
        return f"Donation confirmed: id: {self.donationMoney_id}, {self.description}, Amount: {self.cashAmount}"

    def __repr__(self):
        return f"<Donation(description={self.description}, amount={self.cashAmount})>"


class DonationItem(db.Model):
    donationItem_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]
    donation_date: Mapped[date] = date.today()
    donation_type_id: Mapped[int] = mapped_column(ForeignKey('donation_type.id'))
    amount: Mapped[float]
    donor_id: Mapped[int] = mapped_column(ForeignKey('donor.donor_id'))
    donor: Mapped["Donor"] = relationship(back_populates="donations_items")
    charity_campaign_id: Mapped[int] = mapped_column(ForeignKey('organization_charity_campaign.id'))
    charity_campaign = relationship('OrganizationCharityCampaign')
    donation_type = relationship('DonationType')

    def return_confirmation(self) -> str:
        return f"Donation confirmed: id: {self.donationItem_id}, {self.description}, Number: {self.amount}"

    def __repr__(self):
        return f"<Donation(description={self.description}, amount={self.amount})>"


class DonationType(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]
