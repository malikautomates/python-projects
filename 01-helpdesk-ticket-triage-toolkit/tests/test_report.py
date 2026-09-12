import csv
from datetime import datetime
from pathlib import Path

from triage import report
from triage.models import Ticket


def test_load_tickets_reads_expected_fields(tmp_path: Path):
    csv_path = tmp_path / "tickets.csv"
    csv_path.write_text(
        "ticket_id,subject,description,requester,submitted_at,status\n"
        "T-1,Cannot log in,Password not working,ayo@vortexai654.onmicrosoft.com,2026-09-10 09:00,Open\n",
        encoding="utf-8",
    )
    tickets = report.load_tickets(csv_path)
    assert len(tickets) == 1
    assert tickets[0].ticket_id == "T-1"
    assert tickets[0].submitted_at == datetime(2026, 9, 10, 9, 0)


def test_summarize_counts_categories_and_priorities():
    now = datetime(2026, 9, 12, 12, 0)
    tickets = [
        Ticket("T-1", "urgent VPN down for the entire team", "", "a@x.com", now, "Open"),
        Ticket("T-2", "password reset needed", "", "b@x.com", now, "Open"),
    ]
    triaged = report.triage_all(tickets, now=now)
    summary = report.summarize(triaged)
    assert summary["total"] == 2
    assert summary["by_category"]["Network & Connectivity"] == 1
    assert summary["by_category"]["Account & Access"] == 1
    assert summary["by_priority"]["High"] == 1


def test_summarize_collects_only_breached_tickets():
    now = datetime(2026, 9, 12, 12, 0)
    old = now.replace(hour=0)
    tickets = [
        Ticket("T-1", "urgent VPN down for the entire team", "", "a@x.com", old, "Open"),  # High, 12h old -> breach
        Ticket("T-2", "password reset needed", "", "b@x.com", now, "Open"),  # Medium, fresh -> no breach
    ]
    summary = report.summarize(report.triage_all(tickets, now=now))
    assert [t.ticket_id for t in summary["sla_breaches"]] == ["T-1"]


def test_export_csv_round_trip(tmp_path: Path):
    now = datetime(2026, 9, 12, 12, 0)
    tickets = [Ticket("T-1", "urgent VPN down for entire team", "", "a@x.com", now, "Open")]
    triaged = report.triage_all(tickets, now=now)
    out_path = tmp_path / "out.csv"
    report.export_csv(triaged, out_path)

    with out_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["ticket_id"] == "T-1"
    assert rows[0]["category"] == "Network & Connectivity"
    assert rows[0]["priority"] == "High"
