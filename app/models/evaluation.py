from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Evaluation(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    score: Mapped[int] = mapped_column(CheckConstraint('score >= 1 AND score <= 5'), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    def __repr__(self):
        return f'<Evaluation(id={self.id!r}, score={self.score!r}, description={self.description!r})>'
