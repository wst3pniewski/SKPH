from typing import TYPE_CHECKING, List

from dns.tsig import BadSignature
from flask import current_app
from flask_login import UserMixin
from itsdangerous import SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

if TYPE_CHECKING:
    from .notification import Notification
    from .volunteer import Volunteer
    from .organization import Organization
    from .donor import Donor
    from .affected import Affected
    from .authorities import Authorities


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    USER_TYPES = ('volunteer', 'organization', 'donor', 'affected', 'authorities', 'admin')

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    active: Mapped[bool] = mapped_column(default=True)
    type: Mapped[str] = mapped_column(Enum(*USER_TYPES, name='user_type'), nullable=False)
    totp_secret: Mapped[str] = mapped_column(String(32), unique=True, nullable=True)
    profile_picture: Mapped[str] = mapped_column(String(256), nullable=True)

    volunteer: Mapped["Volunteer"] = relationship(backref='user', uselist=False)
    organization: Mapped["Organization"] = relationship(backref='user', uselist=False)
    donor: Mapped["Donor"] = relationship(backref='user', uselist=False)
    affected: Mapped["Affected"] = relationship(backref='user', uselist=False)
    authorities: Mapped["Authorities"] = relationship(backref='user', uselist=False)
    notifications: Mapped[List["Notification"]] = relationship(back_populates='user',
                                                               cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, type={self.type}, active={self.active})>"

    def get_reset_password_token(self):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

        return serializer.dumps(self.email, salt=self.password_hash)

    @staticmethod
    def validate_reset_password_token(token, user_id):
        user = db.session.get(User, user_id)

        if user is None:
            return None

        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            token_user_email = serializer.loads(
                token,
                max_age=1000 * 60 * 15,
                salt=user.password_hash
            )
        except (BadSignature, SignatureExpired):
            return None

        if token_user_email != user.email:
            return None

        return user
