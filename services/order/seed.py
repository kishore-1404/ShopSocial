import random
import json
from sqlalchemy.orm import sessionmaker
from models import Base, Order
from app import engine

Session = sessionmaker(bind=engine)
session = Session()

USER_IDS = list(range(1, 7))  # 6 users
PRODUCT_IDS = list(range(1, 101))  # 100 products

STATUSES = ["pending", "shipped", "delivered", "cancelled"]

def seed_orders(n=20):
    for _ in range(n):
        user_id = random.choice(USER_IDS)
        product_ids = random.sample(PRODUCT_IDS, random.randint(1, 5))
        total = round(random.uniform(20, 1000), 2)
        status = random.choice(STATUSES)
        order = Order.from_data(user_id, product_ids, total, status)
        session.add(order)
    session.commit()
    print(f"Seeded {n} orders.")

def main():
    Base.metadata.create_all(bind=engine)
    seed_orders(20)

if __name__ == "__main__":
    main()
