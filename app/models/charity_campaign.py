from sqlalchemy import ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

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
    name: Mapped[str]
    description: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    authority = relationship('Authorities')
    authorities_id = mapped_column(ForeignKey('authorities.id'), nullable=False)
    organizations = relationship('Organization',
                                 secondary=organization_campaign_association,
                                 back_populates='charity_campaigns')

    def __repr__(self):
        return f'CharityCampaign({self.id=}, {self.name=}, {self.description=}, {self.authority=})'


class OrganizationCharityCampaign(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    charity_campaign = relationship('CharityCampaign')
    organization = relationship('Organization')
    charity_campaign_id: Mapped[int] = mapped_column(ForeignKey('charity_campaign.id'), nullable=False)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organization.id'), nullable=False)
    volunteers = relationship('Volunteer', secondary=volunteer_campaign_association, back_populates='campaigns')
    donations_money = relationship('DonationMoney', back_populates='charity_campaign')
    donations_item = relationship('DonationItem', back_populates='charity_campaign')
    item_stock = relationship('ItemStock', back_populates='organization_charity_campaign')
    requests = relationship('Request', back_populates='charity_campaign')

    def __repr__(self):
        return f'<OrganizationCharityCampaign(charity_campaign_id={self.charity_campaign_id}, organization_id={self.organization_id})>'
