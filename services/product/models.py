from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    products = relationship('Product', back_populates='category')

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship('Category', back_populates='products')
    posts = relationship('ProductPost', back_populates='product')


class ProductPost(Base):
    __tablename__ = 'product_posts'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    user_id = Column(Integer, nullable=False)  # ForeignKey to user service in future
    content = Column(Text, nullable=False)
    timestamp = Column(String(32), nullable=False)  # ISO8601 string for now
    product = relationship('Product', back_populates='posts')
