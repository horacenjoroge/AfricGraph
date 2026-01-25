"""GraphQL query resolvers."""
from typing import List, Optional
import strawberry
from strawberry.types import Info

from src.api.services.business import get_business, search_businesses
from src.graphql.resolvers.context import GraphQLContext
from src.graphql.types.business import BusinessType


@strawberry.type
class Query:
    """GraphQL query root."""

    @strawberry.field
    def business(self, id: str, info: Info) -> Optional[BusinessType]:
        """Get business by ID."""
        context: GraphQLContext = info.context
        # Check permission
        if not context.check_permission("read", "Business", id):
            raise PermissionError("Not authorized to access this business")
        
        business = get_business(id)
        if business:
            return BusinessType.from_domain(business)
        return None

    @strawberry.field
    def businesses(
        self,
        query: Optional[str] = None,
        sector: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        info: Info = strawberry.UNSET,
    ) -> List[BusinessType]:
        """Search businesses."""
        context: GraphQLContext = info.context if info != strawberry.UNSET else None
        # Check permission for search
        if context and not context.check_permission("read", "Business"):
            raise PermissionError("Not authorized to search businesses")
        
        businesses, _ = search_businesses(query=query, sector=sector, limit=limit, offset=offset)
        return [BusinessType.from_domain(b) for b in businesses]
