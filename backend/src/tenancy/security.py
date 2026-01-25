"""Security and data leak prevention for multi-tenancy."""
import re
from typing import Optional, List, Dict, Any
from src.infrastructure.logging import get_logger
from src.tenancy.context import get_current_tenant

logger = get_logger(__name__)

# Patterns that could bypass tenant filtering
DANGEROUS_PATTERNS = [
    r"WHERE\s+.*tenant_id\s*!=",  # Negation of tenant_id
    r"WHERE\s+.*tenant_id\s*IS\s+NULL",  # NULL checks
    r"WHERE\s+.*tenant_id\s*NOT\s+IN",  # NOT IN with tenant_id
    r"MATCH\s+.*WHERE\s+.*tenant_id\s*=",  # Explicit tenant_id in WHERE (should use param)
    r"OPTIONAL\s+MATCH.*tenant_id",  # Optional matches without tenant filter
    r"CALL\s+.*tenant_id",  # Procedure calls that might bypass filters
]

# Allowed patterns (safe operations)
ALLOWED_PATTERNS = [
    r"\$tenant_id",  # Parameterized queries (safe)
    r"tenant_id\s*=\s*\$tenant_id",  # Safe tenant filter
]


class TenantSecurityValidator:
    """Validates queries and operations for tenant isolation security."""
    
    @staticmethod
    def validate_query(query: str, params: Optional[Dict[str, Any]] = None) -> tuple[bool, Optional[str]]:
        """
        Validate that a query is safe for tenant isolation.
        
        Args:
            query: Cypher query to validate
            params: Query parameters
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        query_upper = query.upper()
        
        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                error = f"Query contains potentially unsafe pattern: {pattern}"
                logger.warning("Unsafe query detected", pattern=pattern, query_preview=query[:100])
                return False, error
        
        # If query contains MATCH, ensure it has tenant filtering
        if "MATCH" in query_upper and "WHERE" in query_upper:
            # Check if tenant_id filter is present
            has_tenant_filter = any(
                re.search(allowed, query, re.IGNORECASE)
                for allowed in ALLOWED_PATTERNS
            )
            
            # Also check if tenant_id is in params
            has_tenant_param = params and "tenant_id" in params
            
            if not (has_tenant_filter or has_tenant_param):
                # Allow if skip_tenant_filter was explicitly set (handled by caller)
                logger.debug("Query without explicit tenant filter", query_preview=query[:100])
        
        return True, None
    
    @staticmethod
    def validate_tenant_context() -> tuple[bool, Optional[str]]:
        """
        Validate that tenant context is properly set.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        tenant = get_current_tenant()
        if not tenant:
            return False, "No tenant context available"
        
        if tenant.status != "active":
            return False, f"Tenant {tenant.tenant_id} is not active"
        
        return True, None
    
    @staticmethod
    def audit_query(
        query: str,
        params: Optional[Dict[str, Any]] = None,
        operation: str = "query",
    ) -> None:
        """
        Audit a query for security monitoring.
        
        Args:
            query: Cypher query
            params: Query parameters
            operation: Type of operation
        """
        tenant = get_current_tenant()
        tenant_id = tenant.tenant_id if tenant else None
        
        # Log query for audit (redact sensitive data)
        safe_params = {}
        if params:
            for key, value in params.items():
                if key in ["password", "token", "secret"]:
                    safe_params[key] = "[REDACTED]"
                else:
                    safe_params[key] = value
        
        logger.info(
            "Query audit",
            tenant_id=tenant_id,
            operation=operation,
            query_preview=query[:200],
            has_tenant_param="tenant_id" in (params or {}),
        )


class TenantAccessControl:
    """Access control for tenant operations."""
    
    @staticmethod
    def can_access_tenant(
        user_id: Optional[str],
        tenant_id: str,
        operation: str = "read",
    ) -> bool:
        """
        Check if user can access tenant.
        
        Args:
            user_id: User ID (None for unauthenticated)
            tenant_id: Tenant ID to access
            operation: Operation type (read, write, admin)
            
        Returns:
            True if access is allowed
        """
        # For now, allow access if tenant context matches
        # In production, implement proper user-tenant mapping
        current_tenant = get_current_tenant()
        if current_tenant and current_tenant.tenant_id == tenant_id:
            return True
        
        # Admins can access any tenant (should be checked via role)
        # This is a placeholder - implement proper RBAC
        return False
    
    @staticmethod
    def validate_tenant_operation(
        tenant_id: str,
        operation: str,
        user_id: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that a tenant operation is allowed.
        
        Args:
            tenant_id: Tenant ID
            operation: Operation type
            user_id: User ID performing operation
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Check tenant context
        is_valid, error = TenantSecurityValidator.validate_tenant_context()
        if not is_valid:
            return False, error
        
        # Check access control
        if not TenantAccessControl.can_access_tenant(user_id, tenant_id, operation):
            return False, f"Access denied for tenant {tenant_id}"
        
        return True, None
