"""GraphQL schema definition."""
import strawberry

from src.graphql.resolvers.queries import Query
from src.graphql.resolvers.mutations import Mutation
from src.graphql.resolvers.subscriptions import Subscription
from src.graphql.resolvers.graph import GraphQuery


# Combine all query types
@strawberry.type
class RootQuery(Query, GraphQuery):
    """Root query combining all query types."""
    pass


# Create schema
schema = strawberry.Schema(
    query=RootQuery,
    mutation=Mutation,
    subscription=Subscription,
)
