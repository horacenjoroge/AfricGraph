"""GraphQL mutation resolvers."""
from typing import Optional
import strawberry

from src.api.services.business import create_business, update_business
from src.domain.models.business import Business
from src.graphql.resolvers.context import GraphQLContext
from src.graphql.types.business import BusinessType


@strawberry.input
class BusinessCreateInput:
    """Input for creating a business."""

    id: str
    name: str
    registration_number: Optional[str] = None
    sector: Optional[str] = None


@strawberry.input
class BusinessUpdateInput:
    """Input for updating a business."""

    name: Optional[str] = None
    registration_number: Optional[str] = None
    sector: Optional[str] = None


@strawberry.type
class Mutation:
    """GraphQL mutation root."""

    @strawberry.mutation
    def create_business(
        self,
        input: BusinessCreateInput,
        info: strawberry.Info,
    ) -> BusinessType:
        """Create a new business."""
        context: GraphQLContext = info.context
        # Check permission
        if not context.check_permission("create", "Business"):
            raise PermissionError("Not authorized to create businesses")
        
        business = Business(
            id=input.id,
            name=input.name,
            registration_number=input.registration_number,
            sector=input.sector,
        )
        create_business(business)
        return BusinessType.from_domain(business)

    @strawberry.mutation
    def update_business(
        self,
        business_id: str,
        input: BusinessUpdateInput,
        info: strawberry.Info,
    ) -> Optional[BusinessType]:
        """Update a business."""
        context: GraphQLContext = info.context
        # Check permission
        if not context.check_permission("update", "Business", business_id):
            raise PermissionError("Not authorized to update this business")
        
        updates = input.__dict__
        updates = {k: v for k, v in updates.items() if v is not None}
        
        business = update_business(business_id, updates)
        if business:
            return BusinessType.from_domain(business)
        return None
