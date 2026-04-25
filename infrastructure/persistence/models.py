
from flask_sqlalchemy import SQLAlchemy
from pgvector.sqlalchemy import Vector

db = SQLAlchemy()

class FruitTable(db.Model):
    __tablename__ = 'fruits'
    fruit_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)

class ImageTable(db.Model):
    __tablename__ = 'images'
    image_id = db.Column(db.Integer, primary_key=True)
    fruit_id = db.Column(db.Integer, db.ForeignKey('fruits.fruit_id'))
    filename = db.Column(db.String(30))
    filepath = db.Column(db.String(100))

class FeatureTable(db.Model):
    __tablename__ = 'features'
    feature_id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('images.image_id'))
    color = db.Column(Vector(256))
    color_moments = db.Column(Vector(9))
    texture = db.Column(Vector(10))
    glcm = db.Column(Vector(4))
    shape = db.Column(Vector(7))