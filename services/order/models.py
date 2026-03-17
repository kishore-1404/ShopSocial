from enum import Enum
from dataclasses import dataclass, field
from typing import List
from datetime import datetime

class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class Order:
    id: int
    user_id: int
    product_ids: List[int]
    total: float
    status: OrderStatus = OrderStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
