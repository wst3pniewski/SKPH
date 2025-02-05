from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.extensions import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    user = relationship('User', back_populates='notifications')

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, message={self.message}, is_read={self.is_read})>"
