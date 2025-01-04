import enum

class StatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BANNED = "banned"
    DELETED = "deleted"
    PENDING = "pending"

class AccessLevelEnum(str, enum.Enum):
    ORG_LEVEL = "ORG_LEVEL"  # Accessible organization-wide
    TEAM_LEVEL = "TEAM_LEVEL"  # Only accessible by specific teams
    HYBRID = "HYBRID"  # Accessible at both levels