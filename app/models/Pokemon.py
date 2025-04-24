# Define the Pokémon model
from app.db import db


class Pokemon(db.Model):
    __tablename__ = 'pokemon'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    number = db.Column(db.Integer)
    name = db.Column(db.String)
    type_one = db.Column(db.String)
    type_two = db.Column(db.String)
    total = db.Column(db.Integer)
    hit_points = db.Column(db.Integer)
    attack = db.Column(db.Integer)
    defense = db.Column(db.Integer)
    special_attack = db.Column(db.Integer)
    special_defense = db.Column(db.Integer)
    speed = db.Column(db.Integer)
    generation = db.Column(db.Integer)
    legendary = db.Column(db.Boolean)

    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'name': self.name,
            'type_one': self.type_one,
            'type_two': self.type_two,
            'total': self.total,
            'hit_points': self.hit_points,
            'attack': self.attack,
            'defense': self.defense,
            'special_attack': self.special_attack,
            'special_defense': self.special_defense,
            'speed': self.speed,
            'generation': self.generation,
            'legendary': self.legendary,
            'icon': f"https://img.pokemondb.net/sprites/silver/normal/{self.name.lower()}.png",
            'image': f"https://img.pokemondb.net/artwork/{self.name.lower()}.jpg"
        }
