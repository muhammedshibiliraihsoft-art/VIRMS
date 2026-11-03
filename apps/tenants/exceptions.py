from django.core.exceptions import ValidationError


class CompanyModuleStateConflict(ValidationError):
    """A concurrent or stale module-state change requires a fresh read."""
