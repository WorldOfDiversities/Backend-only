from rest_framework.permissions import SAFE_METHODS, BasePermission


class BaseRolePermission(BasePermission):
    allowed_roles: set[str] = set()
    allow_read_for_authenticated: bool = False

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if self.allow_read_for_authenticated and request.method in SAFE_METHODS:
            return True

        role = getattr(getattr(user, "profile", None), "role", None)
        return role in self.allowed_roles


class IsAdminRole(BaseRolePermission):
    allowed_roles = {"ADMIN"}


class IsAdminOrManager(BaseRolePermission):
    allowed_roles = {"ADMIN", "MANAGER"}


class IsAdminManagerOrReadOnly(BaseRolePermission):
    allowed_roles = {"ADMIN", "MANAGER"}
    allow_read_for_authenticated = True


class IsStaffRole(BaseRolePermission):
    allowed_roles = {"ADMIN", "MANAGER", "CASHIER"}
