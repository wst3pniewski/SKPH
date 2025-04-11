from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from .evaluation import Evaluation
    from .volunteer import Volunteer


class Task(db.Model):

    AVAILABLE_STATUS = ('completed', 'ongoing', 'rejected')

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    status = mapped_column(Enum(*AVAILABLE_STATUS, name='task_status'), default='ongoing', nullable=False)
    charity_campaign_id: Mapped[int] = mapped_column(ForeignKey('organization_charity_campaign.id'))
    volunteer_id: Mapped[int] = mapped_column(ForeignKey('volunteer.id'))
    evaluation_id: Mapped[int] = mapped_column(ForeignKey('evaluation.id'), nullable=True)

    evaluation_: Mapped["Evaluation"] = relationship()
    volunteer: Mapped["Volunteer"] = relationship(back_populates='tasks')

    def __repr__(self):
        return (
            f'<Task:(id={self.id!r}, name={self.name!r}, '
            f'description={self.description!r}, volunteer_id={self.volunteer_id!r})>'
        )
