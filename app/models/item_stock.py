from typing import TYPE_CHECKING, List
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from .charity_campaign import OrganizationCharityCampaign
    from .donation import DonationType


class ItemStock(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    item_type_id: Mapped[int] = mapped_column(ForeignKey('donation_type.id'), nullable=False)
    item_type: Mapped["DonationType"] = relationship()
    amount: Mapped[int] = mapped_column(nullable=False)
    organization_charity_campaign_id: Mapped[int] = mapped_column(ForeignKey('organization_charity_campaign.id'))
    organization_charity_campaign: Mapped[List["OrganizationCharityCampaign"]] = relationship()

    def __repr__(self):
        return f'<ItemStock(id={self.id!r}, item_type_id={self.item_type_id!r}, amount={self.amount!r}, \
                organization_charity_campaign_id={self.organization_charity_campaign_id!r})>'
