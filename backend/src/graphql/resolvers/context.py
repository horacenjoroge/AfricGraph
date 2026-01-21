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
        """Check if subject has permission using ABAC engine."""
        if not self.subject:
            return False
        
        try:
            from src.security.abac.engine import AbacEngine
            from src.security.abac.attributes import ResourceAttributes, EnvironmentAttributes
            from src.security.abac.policies import Action
            from datetime import datetime
            
            # Map action string to Action enum
            action_map = {
                "read": Action.READ,
                "create": Action.CREATE,
                "update": Action.UPDATE,
                "delete": Action.DELETE,
            }
            abac_action = action_map.get(action, Action.READ)
            
            # Build resource attributes
            resource = ResourceAttributes(
                type=resource_type,
                id=resource_id,
                business_id=resource_id if resource_type == "Business" else None,
                sensitivity_level="public",  # Default, could be extracted from resource
            )
            
            # Build environment attributes (simplified)
            environment = EnvironmentAttributes(
                time=datetime.now(),
                location=None,
                ip_address=None,
            )
            
            # Use ABAC engine
            engine = AbacEngine()
            result = engine.authorize(
                subject=self.subject,
                action=abac_action,
                resource=resource,
                environment=environment,
            )
            return result.authorized
        except Exception:
            # Fallback to simple check if ABAC fails
            if self.subject.role == "admin":
                return True
            if resource_type == "Business" and resource_id and self.subject.business_id == resource_id:
                return True
            if self.subject.role == "analyst" and action == "read":
                return True
            return False
