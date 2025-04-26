# Define the Captured model
from app.repository import db
from datetime import datetime


class Captured(db.Model):
    __tablename__ = 'captured'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_created = db.Column(db.DateTime, default=datetime.now())
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemon.id'), nullable=False)
    
    # Define relationships
    user = db.relationship('User', backref=db.backref('captures', lazy=True))
    pokemon = db.relationship('Pokemon', backref=db.backref('captures', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'date_created': self.date_created.isoformat() if self.date_created else None,
            'user_id': self.user_id,
            'pokemon_id': self.pokemon_id
        }