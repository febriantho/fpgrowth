from enum import unique
from . import db
from flask_login import UserMixin   
from dataclasses import dataclass 
from datetime import date

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

@dataclass
class Product(db.Model):
    id: str
    name: str
    price: int 
    unit: str
    type: str
    stock: int

    id = db.Column(db.String(150), primary_key=True)
    name = db.Column(db.String(150))
    price = db.Column(db.Integer)
    unit = db.Column(db.String(150))
    type = db.Column(db.String(150))
    stock = db.Column(db.Integer)

    def __repr__(self):
        return '<Name %r>' % self.id

@dataclass
class Service(db.Model):
    id: str
    name: str
    price: int 
    type: str
    id = db.Column(db.String(150), primary_key=True)
    name = db.Column(db.String(150))
    price = db.Column(db.Integer)
    type = db.Column(db.String(150))

    def __repr__(self):
        return '<Name %r>' % self.id


class Parameter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    value = db.Column(db.String(150))

    def __repr__(self):
        return '<Name %r>' % self.id


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(150))
    date = db.Column(db.Date, default=date.today)
    products = db.Column(db.Text)
    qtt = db.Column(db.Text)
    price = db.Column(db.Text)
    total = db.Column(db.Integer)

    def __repr__(self):
        return '<Name %r>' % self.id
