# Define the User model
from app.repository import db
import uuid
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now())

    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }