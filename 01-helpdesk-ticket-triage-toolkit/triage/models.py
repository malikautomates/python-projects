"""Data model for a single helpdesk ticket as it moves through triage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Ticket:
    ticket_id: str
    subject: str
    description: str
    requester: str
    submitted_at: datetime
    status: str
    category: str = ""
    priority: str = ""
    sla_due: datetime | None = None
    sla_breached: bool = False

    @property
    def text(self) -> str:
        """Combined subject + description, used for keyword matching."""
        return f"{self.subject} {self.description}".lower()
