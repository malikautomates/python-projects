from datetime import datetime, timedelta

import pytest

from triage.models import Ticket
from triage.rules import (
    DEFAULT_CATEGORY,
    DEFAULT_PRIORITY,
    categorize,
    compute_sla,
    prioritize,
    triage,
)


def make_ticket(subject="", description="", status="Open", submitted_at=None) -> Ticket:
    return Ticket(
        ticket_id="T-TEST",
        subject=subject,
        description=description,
        requester="test.user@vortexai654.onmicrosoft.com",
        submitted_at=submitted_at or datetime.now(),
        status=status,
    )


@pytest.mark.parametrize(
    "text, expected",
    [
        ("I forgot my password and I'm locked out", "Account & Access"),
        ("Outlook keeps crashing when I open an email", "Microsoft 365"),
        ("The VPN won't connect from home", "Network & Connectivity"),
        ("My laptop won't turn on this morning", "Hardware"),
        ("Got a suspicious phishing email asking for my login", "Security"),
        ("The nightly batch report needs formatting fixed", DEFAULT_CATEGORY),
    ],
)
def test_categorize(text, expected):
    assert categorize(make_ticket(subject=text)) == expected


def test_categorize_is_case_insensitive():
    assert categorize(make_ticket(subject="PASSWORD RESET NEEDED")) == "Account & Access"


def test_security_keyword_wins_over_account_access_when_both_present():
    # "phishing" (Security) and "password" (Account & Access) both appear.
    # Security is checked first in CATEGORY_KEYWORDS, so it should win.
    ticket = make_ticket(subject="Phishing email asking for my password")
    assert categorize(ticket) == "Security"


@pytest.mark.parametrize(
    "text, expected",
    [
        ("URGENT the file server is down for the entire team", "High"),
        ("No rush, just a question about signature formatting", "Low"),
        ("Can someone update my desk phone extension", DEFAULT_PRIORITY),
    ],
)
def test_prioritize(text, expected):
    assert prioritize(make_ticket(subject=text)) == expected


def test_high_priority_keyword_wins_over_low_priority_keyword():
    ticket = make_ticket(subject="Urgent, but no rush if you're busy")
    assert prioritize(ticket) == "High"


def test_sla_breach_only_applies_to_open_tickets():
    submitted = datetime.now() - timedelta(hours=10)
    ticket = make_ticket(status="Closed", submitted_at=submitted)
    ticket.priority = "High"  # 4-hour SLA, 10 hours old -> would breach if open
    _, breached = compute_sla(ticket, datetime.now())
    assert breached is False


def test_sla_breach_flagged_for_overdue_open_ticket():
    submitted = datetime.now() - timedelta(hours=10)
    ticket = make_ticket(status="Open", submitted_at=submitted)
    ticket.priority = "High"
    _, breached = compute_sla(ticket, datetime.now())
    assert breached is True


def test_sla_not_breached_exactly_at_due_time():
    submitted = datetime(2026, 1, 1, 9, 0)
    ticket = make_ticket(status="Open", submitted_at=submitted)
    ticket.priority = "High"
    _, breached = compute_sla(ticket, now=submitted + timedelta(hours=4))
    assert breached is False


def test_triage_populates_category_priority_and_sla():
    ticket = make_ticket(subject="Urgent: VPN is down for the entire team", status="Open")
    result = triage(ticket, now=datetime.now())
    assert result.category == "Network & Connectivity"
    assert result.priority == "High"
    assert result.sla_due is not None
