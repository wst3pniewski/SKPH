from enum import Enum

from flask_babel import lazy_gettext as _
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLEnum

from app.extensions import db


class RequestStatus(Enum):
    PENDING = _("Pending")
    APPROVED = _("Approved")
    REJECTED = _("Not approved")
    COMPLETED = _("Completed")


class Request(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    amount: Mapped[int]
    status: Mapped[RequestStatus] = mapped_column(SQLEnum(RequestStatus), nullable=False)
    address = relationship('Address')
    address_id = mapped_column(ForeignKey('address.id'))
    affected_id = mapped_column(ForeignKey('affected.id'))
    donation_type_id = mapped_column(ForeignKey('donation_type.id'))
    charity_campaign_id = mapped_column(ForeignKey('organization_charity_campaign.id'))

    affected = relationship('Affected', back_populates='requests')
    donation_type = relationship('DonationType')
    charity_campaign = relationship('OrganizationCharityCampaign', back_populates='requests')

    def __repr__(self):
        return (
            f'Request:(id={self.id!r}, name={self.name!r}, '
            f'amount={self.amount!r}, status={self.status.value!r},'
            f'address={self.address!r}, affected_id={self.affected_id!r})'
        )
