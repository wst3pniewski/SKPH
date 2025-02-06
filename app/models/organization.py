from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

from .charity_campaign import organization_campaign_association

if TYPE_CHECKING:
    from .address import Address
    from .charity_campaign import CharityCampaign


class Organization(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column(default=False)
    address: Mapped["Address"] = relationship()
    address_id: Mapped[int] = mapped_column(ForeignKey('address.id'))
    charity_campaigns: Mapped[List["CharityCampaign"]] = relationship(secondary=organization_campaign_association,
                                                                      back_populates='organizations')
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    def get_approve_status(self):
        return self.approved

    def approve(self):
        self.approved = True
        db.session.commit()

    def disapprove(self):
        self.approved = False
        db.session.commit()

    def __repr__(self):
        return f'<Organization(id={self.id!r}, organization_name={self.organization_name!r}, \
                description={self.description!r}, approved={self.approved!r}, \
                address={self.address!r}, charity_campaigns={self.charity_campaigns!r})>'
