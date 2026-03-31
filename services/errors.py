"""Service-layer exceptions used across business workflows."""


class ServiceError(Exception):
    """Base class for expected business/service failures."""


class ValidationServiceError(ServiceError):
    """Raised when input validation fails at the service layer."""


class BusinessRuleError(ServiceError):
    """Raised when business invariants are violated."""


class InventoryError(BusinessRuleError):
    """Raised when stock operations fail."""


class OrchestrationError(ServiceError):
    """Raised when a multi-step workflow fails unexpectedly."""
