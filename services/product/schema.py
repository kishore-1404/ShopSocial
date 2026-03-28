import graphene
from graphene import ObjectType, Field, List, Int, String, Float
from graphql import GraphQLError

from service import list_categories, list_posts, list_products, search_products


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
        return list_products(db)

    def resolve_categories(self, info):
        db = info.context['db']
        return list_categories(db)

    def resolve_posts(self, info):
        db = info.context['db']
        return list_posts(db)

    def resolve_searchProducts(self, info, name=None, categoryId=None):
        if categoryId is not None and categoryId <= 0:
            raise GraphQLError("categoryId must be a positive integer")

        normalized_name = None
        if name is not None:
            normalized_name = name.strip()
            if len(normalized_name) > 200:
                raise GraphQLError("name must be 200 characters or fewer")
            if not normalized_name:
                normalized_name = None

        db = info.context['db']
        return search_products(db, name=normalized_name, category_id=categoryId)

schema = graphene.Schema(query=Query)
