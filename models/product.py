from flask_sqlalchemy import SQLAlchemy
import sqlite3
db = SQLAlchemy()

class Product:
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    def __init__(self, name, sku, quantity, price):
        self.name = name
        self.sku = sku
        self.quantity = quantity
        self.price = price

    def __repr__(self):
        return f'<Product {self.name} (SKU: {self.sku})>'