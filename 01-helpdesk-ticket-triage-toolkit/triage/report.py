"""Loading, summarizing, exporting, and rendering triaged tickets."""

from __future__ import annotations

import csv
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .models import Ticket
from .rules import triage

logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%d %H:%M"


def load_tickets(csv_path: Path) -> list[Ticket]:
    tickets: list[Ticket] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            tickets.append(
                Ticket(
                    ticket_id=row["ticket_id"],
                    subject=row["subject"],
                    description=row["description"],
                    requester=row["requester"],
                    submitted_at=datetime.strptime(row["submitted_at"], DATE_FORMAT),
                    status=row["status"],
                )
            )
    logger.info("Loaded %d tickets from %s", len(tickets), csv_path)
    return tickets


def triage_all(tickets: list[Ticket], now: datetime | None = None) -> list[Ticket]:
    now = now or datetime.now()
    return [triage(t, now) for t in tickets]


def summarize(tickets: list[Ticket]) -> dict:
    breaches = [t for t in tickets if t.sla_breached]
    logger.info(
        "Summarized %d tickets: %d SLA breach(es)", len(tickets), len(breaches)
    )
    return {
        "total": len(tickets),
        "by_category": Counter(t.category for t in tickets),
        "by_priority": Counter(t.priority for t in tickets),
        "sla_breaches": breaches,
    }


def export_csv(tickets: list[Ticket], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "ticket_id", "subject", "requester", "status",
                "category", "priority", "submitted_at", "sla_due", "sla_breached",
            ]
        )
        for t in tickets:
            writer.writerow(
                [
                    t.ticket_id, t.subject, t.requester, t.status,
                    t.category, t.priority,
                    t.submitted_at.strftime(DATE_FORMAT),
                    t.sla_due.strftime(DATE_FORMAT) if t.sla_due else "",
                    t.sla_breached,
                ]
            )
    logger.info("Wrote triaged export to %s", path)


def render_console_report(tickets: list[Ticket], summary: dict, console: Console) -> None:
    console.rule("[bold]Helpdesk Ticket Triage Report[/bold]")
    console.print(f"Total tickets processed: [bold]{summary['total']}[/bold]\n")

    category_table = Table(title="Tickets by Category")
    category_table.add_column("Category")
    category_table.add_column("Count", justify="right")
    for category, count in summary["by_category"].most_common():
        category_table.add_row(category, str(count))
    console.print(category_table)

    priority_table = Table(title="Tickets by Priority")
    priority_table.add_column("Priority")
    priority_table.add_column("Count", justify="right")
    for priority in ("High", "Medium", "Low"):
        priority_table.add_row(priority, str(summary["by_priority"].get(priority, 0)))
    console.print(priority_table)

    breaches = summary["sla_breaches"]
    if breaches:
        breach_table = Table(
            title=f"SLA Breaches — open tickets past their response window ({len(breaches)})",
            style="red",
        )
        breach_table.add_column("Ticket ID")
        breach_table.add_column("Priority")
        breach_table.add_column("Requester")
        breach_table.add_column("SLA Due")
        breach_table.add_column("Subject")
        for t in sorted(breaches, key=lambda x: x.sla_due):
            breach_table.add_row(
                t.ticket_id, t.priority, t.requester,
                t.sla_due.strftime(DATE_FORMAT), t.subject,
            )
        console.print(breach_table)
    else:
        console.print("[green]No SLA breaches among open tickets.[/green]")


def generate_charts(summary: dict, output_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    categories = summary["by_category"].most_common()
    if categories:
        labels, values = zip(*categories)
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.barh(labels, values, color="#2f6db3")
        ax.invert_yaxis()
        ax.set_xlabel("Ticket count")
        ax.set_title("Tickets by Category")
        fig.tight_layout()
        path = output_dir / "category-breakdown.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        paths.append(path)

    priority_order = ["High", "Medium", "Low"]
    values = [summary["by_priority"].get(p, 0) for p in priority_order]
    colors = ["#c0392b", "#e2a33d", "#3f8f5f"]
    fig, ax = plt.subplots(figsize=(5, 4.5))
    ax.bar(priority_order, values, color=colors)
    ax.set_ylabel("Ticket count")
    ax.set_title("Tickets by Priority")
    fig.tight_layout()
    path = output_dir / "priority-breakdown.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    paths.append(path)

    logger.info("Wrote %d chart(s) to %s", len(paths), output_dir)
    return paths
