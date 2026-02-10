from enum import Enum


class Role(Enum):
    """
    Enumeration for User Roles.

    This enumeration represents various roles that a user can have in the system.
    Each role is associated with a string value that describes the role.

    Attributes:
        ADMIN (str): Represents an administrative role.
        USER (str): Represents a standard user role.
        GUEST (str): Represents a guest user role.
    """

    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"
    PTI = "PTI"
    PLANNER = "PLANNER"
    APTI = "APTI"

    def __str__(self):
        return self.value
