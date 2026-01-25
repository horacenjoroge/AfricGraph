"""GraphQL subscription resolvers for real-time updates."""
import strawberry
from strawberry.types import Info
from typing import AsyncIterator
import asyncio

from src.graphql.types.business import BusinessType
from src.graphql.resolvers.context import GraphQLContext


@strawberry.type
class Subscription:
    """GraphQL subscription root."""

    @strawberry.subscription
    async def business_updates(
        self,
        business_id: str,
        info: Info,
    ) -> AsyncIterator[BusinessType]:
        """Subscribe to business updates."""
        context: GraphQLContext = info.context
        # Check permission
        if not context.check_permission("read", "Business", business_id):
            raise PermissionError("Not authorized")
        
        # In a real implementation, this would connect to a message queue
        # or use WebSocket for real-time updates
        # For now, this is a placeholder that demonstrates the pattern
        
        from src.api.services.business import get_business
        
        # Simulate periodic updates (in production, use actual event stream)
        while True:
            business = get_business(business_id)
            if business:
                yield BusinessType.from_domain(business)
            await asyncio.sleep(5)  # Check every 5 seconds

    @strawberry.subscription
    async def risk_score_updates(
        self,
        business_id: str,
        info: Info,
    ) -> AsyncIterator[float]:
        """Subscribe to risk score updates for a business."""
        context: GraphQLContext = info.context
        if not context.check_permission("read", "Business", business_id):
            raise PermissionError("Not authorized")
        
        # Placeholder - would connect to actual risk score update stream
        from src.risk.scoring.history import get_latest_risk_score
        
        while True:
            risk_score = get_latest_risk_score(business_id)
            if risk_score:
                yield risk_score.score
            await asyncio.sleep(10)  # Check every 10 seconds
