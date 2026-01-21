"""GraphQL context with DataLoaders and permissions."""
from typing import Optional
import strawberry

from src.graphql.dataloaders.business import create_business_loader
from src.graphql.dataloaders.person import create_person_loader
from src.security.abac.attributes import SubjectAttributes


@strawberry.type
class GraphQLContext:
    """GraphQL request context."""

    def __init__(self, subject: Optional[SubjectAttributes] = None):
        self.subject = subject
        self.business_loader = create_business_loader()
        self.person_loader = create_person_loader()

    def check_permission(self, action: str, resource_type: str, resource_id: Optional[str] = None) -> bool:
        """Check if subject has permission (simplified - would use ABAC engine)."""
        if not self.subject:
            return False
        # Admin can do everything
        if self.subject.role == "admin":
            return True
        # Business owners can access their own business
        if resource_type == "Business" and resource_id and self.subject.business_id == resource_id:
            return True
        # Analysts can read non-sensitive data
        if self.subject.role == "analyst" and action == "read":
            return True
        return False
