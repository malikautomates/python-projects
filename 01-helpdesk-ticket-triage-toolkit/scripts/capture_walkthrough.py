"""Regenerate every screenshot used in the project README.

Each image is a real capture of the tool actually running or the actual
source — never a mockup:

- Directory tree, source code, and pytest code are rendered with Rich's
  Syntax/Tree and exported to SVG.
- The CLI --help, the full triage run, and the pytest run are captured by
  actually invoking the program and rendering the real (colored) output to
  SVG with Rich.
- The charts and the triaged-CSV preview are built from the actual output
  of a live run against data/sample_tickets.csv.

Run after any change to triage/, tests/, or data/sample_tickets.csv so the
README images never drift out of sync with the code:

    python scripts/capture_walkthrough.py
"""

from __future__ import annotations

import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS = ROOT / "screenshots"
SCREENSHOTS.mkdir(exist_ok=True)

SKIP_DIRS = {"__pycache__", ".pytest_cache", "output", ".git", "screenshots"}


def new_console() -> Console:
    return Console(record=True, width=104, force_terminal=True)


def save(console: Console, name: str, title: str) -> None:
    path = SCREENSHOTS / name
    console.save_svg(str(path), title=title)
    print(f"Wrote {path}")


def capture_project_structure() -> None:
    tree = Tree("[bold]01-helpdesk-ticket-triage-toolkit/[/bold]")

    def add(dir_path: Path, node: Tree) -> None:
        entries = sorted(
            (p for p in dir_path.iterdir() if p.name not in SKIP_DIRS),
            key=lambda p: (p.is_file(), p.name.lower()),
        )
        for entry in entries:
            if entry.is_dir():
                branch = node.add(f"[bold blue]{entry.name}/[/bold blue]")
                add(entry, branch)
            else:
                node.add(entry.name)

    add(ROOT, tree)

    console = new_console()
    console.print(tree)
    save(console, "01-project-structure.svg", "Project structure")


def capture_source(name: str, path: Path, title: str, line_range: tuple[int, int] | None = None) -> None:
    code = path.read_text(encoding="utf-8")
    syntax = Syntax(
        code, "python", theme="github-dark", line_numbers=True,
        line_range=line_range, word_wrap=False,
    )
    console = new_console()
    console.print(syntax)
    save(console, name, title)


def capture_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "run.py", "--help"],
        cwd=ROOT, capture_output=True, text=True,
    )
    console = new_console()
    console.print(Text(result.stdout))
    save(console, "05-cli-help.svg", "python run.py --help")


def capture_triage_run() -> None:
    sys.path.insert(0, str(ROOT))
    from triage import report

    console = new_console()
    now = datetime.now()

    tickets = report.load_tickets(ROOT / "data" / "sample_tickets.csv")
    tickets = report.triage_all(tickets, now=now)
    summary = report.summarize(tickets)
    report.render_console_report(tickets, summary, console)
    save(console, "06-cli-triage-report.svg", "python run.py -v — Helpdesk Ticket Triage Report")

    chart_paths = report.generate_charts(summary, SCREENSHOTS)
    (SCREENSHOTS / "category-breakdown.png").replace(SCREENSHOTS / "07-category-breakdown.png")
    (SCREENSHOTS / "priority-breakdown.png").replace(SCREENSHOTS / "08-priority-breakdown.png")
    print("Wrote 07-category-breakdown.png and 08-priority-breakdown.png")

    export_path = ROOT / "output" / "tickets_triaged.csv"
    report.export_csv(tickets, export_path)
    capture_csv_preview(export_path)


def capture_csv_preview(csv_path: Path) -> None:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    table = Table(title="output/tickets_triaged.csv (first 8 of 35 rows)")
    for column in ["ticket_id", "category", "priority", "status", "sla_breached"]:
        table.add_column(column)
    for row in rows[:8]:
        table.add_row(row["ticket_id"], row["category"], row["priority"], row["status"], row["sla_breached"])

    console = new_console()
    console.print(table)
    save(console, "09-triaged-csv-preview.svg", "Triaged CSV export (preview)")


def capture_pytest_run() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--color=yes"],
        cwd=ROOT, capture_output=True, text=True,
    )
    console = new_console()
    console.print(Text.from_ansi(result.stdout + result.stderr))
    save(console, "04-pytest-run.svg", "python -m pytest -v — Test Suite")

    if result.returncode != 0:
        print("WARNING: pytest did not exit 0 — check the captured output above.", file=sys.stderr)


if __name__ == "__main__":
    capture_project_structure()
    capture_source(
        "02-rules-code.svg", ROOT / "triage" / "rules.py",
        "triage/rules.py — categorization, priority, and SLA rules",
    )
    capture_source(
        "03-test-code.svg", ROOT / "tests" / "test_rules.py",
        "tests/test_rules.py — parametrized rule tests", line_range=(1, 34),
    )
    capture_pytest_run()
    capture_cli_help()
    capture_triage_run()
