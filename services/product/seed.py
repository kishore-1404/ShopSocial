import random
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Product, ProductPost
from app import engine
from datetime import datetime

Session = sessionmaker(bind=engine)
session = Session()

# Seed categories
def seed_categories():
    categories = [
        {"name": "Electronics", "description": "Gadgets and devices"},
        {"name": "Books", "description": "All kinds of books"},
        {"name": "Clothing", "description": "Apparel and accessories"},
        {"name": "Home", "description": "Home and kitchen"},
        {"name": "Toys", "description": "Toys and games"},
    ]
    objs = []
    for cat in categories:
        obj = session.query(Category).filter_by(name=cat["name"]).first()
        if not obj:
            obj = Category(**cat)
            session.add(obj)
            objs.append(obj)
    session.commit()
    return session.query(Category).all()

# Seed products
def seed_products(categories, n=50):
    products = []
    for i in range(n):
        cat = random.choice(categories)
        name = f"Product {i+1}"
        description = f"Description for {name}"
        price = round(random.uniform(10, 500), 2)
        prod = Product(name=name, description=description, price=price, category=cat)
        session.add(prod)
        products.append(prod)
    session.commit()
    return session.query(Product).all()

# Seed product posts
def seed_product_posts(products, user_ids):
    for prod in products:
        for _ in range(random.randint(1, 3)):
            post = ProductPost(
                product_id=prod.id,
                user_id=random.choice(user_ids),
                content=f"Post about {prod.name}",
                timestamp=datetime.utcnow().isoformat()
            )
            session.add(post)
    session.commit()

def main():
    Base.metadata.create_all(bind=engine)
    categories = seed_categories()
    products = seed_products(categories, n=100)  # Large product set
    # User IDs will be 1-6 (from user service seed)
    seed_product_posts(products, user_ids=list(range(1, 7)))
    print("Product DB seeded.")

if __name__ == "__main__":
    main()
