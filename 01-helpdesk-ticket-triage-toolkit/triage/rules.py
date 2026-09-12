"""Categorization, prioritization, and SLA rules.

Rule-based rather than ML-based on purpose: every classification decision here
traces to a specific keyword, which means a service desk lead can audit *why*
a ticket landed where it did and adjust a single line to fix a misclassification.
See docs/design-notes.md for the tradeoffs this makes against a trained classifier.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .models import Ticket

# Dict order is the match order: the first category whose keyword appears in
# the ticket text wins. Security is checked first on purpose, so a ticket that
# mentions both "phishing" and "password" is triaged as a security event, not
# a routine password reset.
CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Security": (
        "phishing", "suspicious email", "malware", "virus", "ransomware",
        "unauthorized access", "data breach",
    ),
    "Account & Access": (
        "password", "locked out", "can't log in", "cannot log in", "mfa",
        "authenticator", "access denied", "reset my account", "2fa",
    ),
    "Microsoft 365": (
        "outlook", "teams meeting", "sharepoint", "onedrive", "excel",
        "office 365", "m365", "exchange mailbox", "distribution list",
    ),
    "Network & Connectivity": (
        "vpn", "wifi", "wi-fi", "no internet", "can't connect", "ethernet",
        "slow connection", "network drive", "dns",
    ),
    "Hardware": (
        "printer", "monitor", "laptop", "keyboard", "docking station",
        "webcam", "won't turn on", "battery", "headset",
    ),
    "Software & Applications": (
        "install", "update failed", "keeps crashing", "error message",
        "license key", "won't open", "application", "freezes",
    ),
}

# High is checked before Low, so a ticket carrying both signals ("urgent, but
# no rush") is treated as High. Understating urgency is the safer failure mode
# for a helpdesk than dropping a genuinely urgent ticket into the Low queue.
PRIORITY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "High": (
        "urgent", "asap", "is down", "production", "entire team",
        "cannot work", "outage", "critical", "all users", "can't work",
    ),
    "Low": (
        "when you get a chance", "no rush", "minor", "just a question",
        "cosmetic", "how do i",
    ),
}

# Response-time targets in hours, by priority. Modeled on a typical L1
# helpdesk SLA table; tune to match a real service desk's published targets.
SLA_HOURS: dict[str, int] = {"High": 4, "Medium": 24, "Low": 72}

DEFAULT_CATEGORY = "Other"
DEFAULT_PRIORITY = "Medium"


def categorize(ticket: Ticket) -> str:
    text = ticket.text
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return DEFAULT_CATEGORY


def prioritize(ticket: Ticket) -> str:
    text = ticket.text
    if any(keyword in text for keyword in PRIORITY_KEYWORDS["High"]):
        return "High"
    if any(keyword in text for keyword in PRIORITY_KEYWORDS["Low"]):
        return "Low"
    return DEFAULT_PRIORITY


def compute_sla(ticket: Ticket, now: datetime) -> tuple[datetime, bool]:
    """Return (due timestamp, breached) for an already-prioritized ticket.

    Only open tickets can be breached — a closed ticket that took a while to
    resolve is a lagging-indicator problem for reporting, not an active SLA
    risk that this tool needs to surface.
    """
    due = ticket.submitted_at + timedelta(hours=SLA_HOURS[ticket.priority])
    breached = ticket.status.strip().lower() == "open" and now > due
    return due, breached


def triage(ticket: Ticket, now: datetime | None = None) -> Ticket:
    """Categorize, prioritize, and SLA-check a ticket in place, and return it."""
    now = now or datetime.now()
    ticket.category = categorize(ticket)
    ticket.priority = prioritize(ticket)
    ticket.sla_due, ticket.sla_breached = compute_sla(ticket, now)
    return ticket
