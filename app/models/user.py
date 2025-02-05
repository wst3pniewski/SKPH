from dns.tsig import BadSignature
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from .notification import Notification


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    USER_TYPES = ('volunteer', 'organization', 'donor', 'affected', 'authorities', 'admin')

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    active = db.Column(db.Boolean, default=True)
    type = db.Column(db.Enum(*USER_TYPES, name='user_type'), nullable=False)
    totp_secret = db.Column(db.String(32), unique=True, nullable=True)
    profile_picture = db.Column(db.String(256), nullable=True)

    volunteer = db.relationship('Volunteer', backref='user', uselist=False)
    organization = db.relationship('Organization', backref='user', uselist=False)
    donor = db.relationship('Donor', backref='user', uselist=False)
    affected = db.relationship('Affected', backref='user', uselist=False)
    authorities = db.relationship('Authorities', backref='user', uselist=False)
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, type={self.type}>"

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
