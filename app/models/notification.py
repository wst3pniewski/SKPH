from datetime import datetime
import enum
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, mapped_column, Mapped
from app.extensions import db


class NotificationType(enum.Enum):
    MESSAGE = "message"
    REQUEST = "request"
    TASK = "task"
    DONATION = "donation"


class Notification(db.Model):
    __tablename__ = 'notifications'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    type: Mapped[NotificationType] = mapped_column(nullable=False)

    user = relationship('User', back_populates='notifications')

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, \
                message={self.message}, is_read={self.is_read}, type={self.type})>"
