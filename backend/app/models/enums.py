from enum import Enum


class TestStatus(str, Enum):
    __test__ = False

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"



class ScheduleType(str, Enum):
    INTERVAL = "interval"
    CRON = "cron"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TriggerType(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
