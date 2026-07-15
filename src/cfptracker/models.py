from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class Status(str, Enum):
    WATCHING = "watching"
    DRAFTED = "drafted"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


@dataclass
class Talk:
    title: str
    versions: list[str] = field(default_factory=list)


@dataclass
class Submission:
    id: str
    conference: str
    cfp_deadline: date
    event_date: Optional[date] = None
    talk_title: Optional[str] = None
    talk_version: Optional[str] = None
    status: Status = Status.WATCHING
    url: str = ""
    notes: str = ""
    submitted_date: Optional[date] = None
    decision_date: Optional[date] = None

    def days_until_deadline(self, today: date) -> int:
        return (self.cfp_deadline - today).days

    def is_open(self) -> bool:
        return self.status in (Status.WATCHING, Status.DRAFTED)
