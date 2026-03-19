import graphene
from graphene import ObjectType, Field, List, Int, String, Float
from models import Product, Category, ProductPost


class ProductPostType(graphene.ObjectType):
    id = Int()
    product = Field(lambda: ProductType)
    userId = Int()
    content = String()
    timestamp = String()

    def resolve_userId(self, info):
        return self.user_id

class CategoryType(graphene.ObjectType):
    id = Int()
    name = String()
    description = String()

class ProductType(graphene.ObjectType):
    id = Int()
    name = String()
    description = String()
    price = Float()
    category = Field(CategoryType)


class Query(ObjectType):
    hello = graphene.String(description="A typical hello world")
    products = List(ProductType)
    categories = List(CategoryType)
    posts = List(ProductPostType)
    searchProducts = List(ProductType, name=graphene.String(), categoryId=graphene.Int())

    def resolve_hello(self, info):
        return "Hello, ShopSocial!"

    def resolve_products(self, info):
        db = info.context['db']
        return db.query(Product).all()

    def resolve_categories(self, info):
        db = info.context['db']
        return db.query(Category).all()

    def resolve_posts(self, info):
        db = info.context['db']
        return db.query(ProductPost).all()

    def resolve_searchProducts(self, info, name=None, categoryId=None):
        db = info.context['db']
        query = db.query(Product)
        if name:
            query = query.filter(Product.name.ilike(f"%{name}%"))
        if categoryId:
            query = query.filter(Product.category_id == categoryId)
        return query.all()

schema = graphene.Schema(query=Query)
