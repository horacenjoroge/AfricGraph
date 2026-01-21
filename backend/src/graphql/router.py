"""GraphQL router for FastAPI integration."""
from fastapi import Request
from strawberry.fastapi import GraphQLRouter

from src.graphql.schema import schema
from src.graphql.resolvers.context import GraphQLContext
from src.security.abac.attributes import SubjectAttributes


def get_context(request: Request) -> GraphQLContext:
    """Create GraphQL context from request."""
    # Extract subject attributes from request (simplified)
    # In production, extract from JWT token
    subject = None
    if hasattr(request.state, "abac_subject"):
        subject = request.state.abac_subject
    elif hasattr(request.state, "user"):
        # Fallback: create subject from user if available
        user = request.state.user
        subject = SubjectAttributes(
            user_id=user.get("id"),
            role=user.get("role", "analyst"),
            business_id=user.get("business_id"),
        )
    
    return GraphQLContext(subject=subject)


# Create GraphQL router
graphql_router = GraphQLRouter(
    schema=schema,
    context_getter=get_context,
    graphiql=True,  # Enable GraphiQL playground
)
