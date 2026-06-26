from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class OrderModel(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), nullable=False, index=True)
    item_description = db.Column(db.String(500), nullable=False)
    item_quantity = db.Column(db.Integer, nullable=False)
    item_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_value = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<OrderModel(id={self.id}, user_id={self.user_id})>'
