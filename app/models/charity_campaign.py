from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from .authorities import Authorities
    from .donation import DonationItem, DonationMoney
    from .item_stock import ItemStock
    from .organization import Organization
    from .request import Request
    from .volunteer import Volunteer

volunteer_campaign_association = Table(
    'volunteer_campaign_association',
    db.Model.metadata,
    db.Column('volunteer_id', db.Integer, db.ForeignKey('volunteer.id')),
    db.Column('campaign_id', db.Integer, db.ForeignKey('organization_charity_campaign.id'))
)

organization_campaign_association = Table(
    'organization_campaign_association',
    db.Model.metadata,
    db.Column('campaign_id', db.Integer, db.ForeignKey('charity_campaign.id')),
    db.Column('organization_id', db.Integer, db.ForeignKey('organization.id')),
)


class CharityCampaign(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    authority: Mapped["Authorities"] = relationship()
    authorities_id = mapped_column(ForeignKey('authorities.id'), nullable=False)
    organizations: Mapped[List["Organization"]] = relationship(secondary=organization_campaign_association,
                                                               back_populates='charity_campaigns')

    def __repr__(self):
        return f'CharityCampaign(id={self.id!r}, name={self.name!r}, \
                description={self.description!r}, is_active{self.is_active!r} \
                authorities={self.authority!r}, organizations={self.organizations!r})'


class OrganizationCharityCampaign(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    charity_campaign: Mapped["CharityCampaign"] = relationship()
    organization: Mapped["Organization"] = relationship()
    charity_campaign_id: Mapped[int] = mapped_column(ForeignKey('charity_campaign.id'), nullable=False)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organization.id'), nullable=False)

    volunteers: Mapped[List["Volunteer"]] = relationship(secondary=volunteer_campaign_association,
                                                         back_populates='campaigns')
    donations_money: Mapped[List["DonationMoney"]] = relationship(back_populates='charity_campaign')
    donations_item: Mapped[List["DonationItem"]] = relationship(back_populates='charity_campaign')
    item_stocks: Mapped[List["ItemStock"]] = relationship(back_populates='organization_charity_campaign')
    requests: Mapped[List["Request"]] = relationship(back_populates='charity_campaign')

    def __repr__(self):
        return f'<OrganizationCharityCampaign(id={self.id!r}, charity_campaign_id={self.charity_campaign_id!r}, \
                organization_id={self.organization_id})>'
