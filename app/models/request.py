from enum import Enum
from typing import TYPE_CHECKING

from flask_babel import lazy_gettext as _
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLEnum

from app.extensions import db

if TYPE_CHECKING:
    from .address import Address
    from .affected import Affected
    from .charity_campaign import OrganizationCharityCampaign
    from .donation import DonationType


class RequestStatus(Enum):
    PENDING = _("Pending")
    APPROVED = _("Approved")
    REJECTED = _("Not approved")
    COMPLETED = _("Completed")


class Request(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[RequestStatus] = mapped_column(SQLEnum(RequestStatus), nullable=False)
    address: Mapped["Address"] = relationship()
    address_id: Mapped[int] = mapped_column(ForeignKey('address.id'))
    affected_id: Mapped[int] = mapped_column(ForeignKey('affected.id'))
    donation_type_id: Mapped[int] = mapped_column(ForeignKey('donation_type.id'))
    charity_campaign_id: Mapped[int] = mapped_column(ForeignKey('organization_charity_campaign.id'))

    affected: Mapped["Affected"] = relationship(back_populates='requests')
    donation_type: Mapped["DonationType"] = relationship()
    charity_campaign: Mapped["OrganizationCharityCampaign"] = relationship(back_populates='requests')

    def __repr__(self):
        return (
            f'<Request:(id={self.id!r}, name={self.name!r}, '
            f'amount={self.amount!r}, status={self.status.value!r},'
            f'address={self.address!r}, affected_id={self.affected_id!r})>'
        )
