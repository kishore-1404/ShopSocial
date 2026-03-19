from sqlalchemy import Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime
import json

Base = declarative_base()

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    product_ids = Column(Text, nullable=False)  # Store as JSON string
    total = Column(Float, nullable=False)
    status = Column(String(32), nullable=False, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_ids': json.loads(self.product_ids),
            'total': self.total,
            'status': self.status,
            'created_at': self.created_at.isoformat() + 'Z'
        }

    @staticmethod
    def from_data(user_id, product_ids, total, status='pending'):
        return Order(
            user_id=user_id,
            product_ids=json.dumps(product_ids),
            total=total,
            status=status
        )
