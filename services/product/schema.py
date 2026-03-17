import graphene
from graphene import ObjectType, Field, List, Int, String, Float
from models import Product, Category, ProductPost

# In-memory store for demonstration (replace with DB session in production)
_CATEGORIES = [
    Category(id=1, name="Electronics", description="Gadgets and devices"),
    Category(id=2, name="Clothing", description="Apparel and accessories"),
]

_PRODUCTS = [
    Product(id=1, name="Smartphone", description="Latest model", price=699.99, category=_CATEGORIES[0]),
    Product(id=2, name="T-Shirt", description="100% cotton", price=19.99, category=_CATEGORIES[1]),
]

_POSTS = [
    ProductPost(id=1, product_id=1, user_id=101, content="Great phone!", timestamp="2026-03-16T10:00:00Z", product=_PRODUCTS[0]),
    ProductPost(id=2, product_id=2, user_id=102, content="Love this shirt!", timestamp="2026-03-16T11:00:00Z", product=_PRODUCTS[1]),
]
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
        return _PRODUCTS

    def resolve_categories(self, info):
        return _CATEGORIES

    def resolve_posts(self, info):
        return _POSTS

    def resolve_searchProducts(self, info, name=None, categoryId=None):
        results = _PRODUCTS
        if name:
            results = [p for p in results if name.lower() in p.name.lower()]
        if categoryId:
            results = [p for p in results if p.category and p.category.id == categoryId]
        return results

schema = graphene.Schema(query=Query)
