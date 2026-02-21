"""Domain enumerations for bill verification."""

import enum


class BillStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class VerificationFlag(str, enum.Enum):
    OK = "OK"
    OVERCHARGED = "OVERCHARGED"
    DUPLICATE = "DUPLICATE"
    MATH_ERROR = "MATH_ERROR"
    UNKNOWN = "UNKNOWN"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
