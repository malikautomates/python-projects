"""Command-line entry point: load a ticket CSV, triage it, report the results."""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

from rich.console import Console

from . import report

DEFAULT_INPUT = Path("data/sample_tickets.csv")
DEFAULT_OUTPUT_DIR = Path("output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="triage",
        description="Categorize, prioritize, and SLA-check helpdesk tickets from a CSV export.",
    )
    parser.add_argument(
        "--input", type=Path, default=DEFAULT_INPUT,
        help=f"Path to a ticket CSV export (default: {DEFAULT_INPUT}).",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for the triaged CSV, charts, and log (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--no-charts", action="store_true",
        help="Skip generating category/priority chart images.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Also print debug-level logging to the console.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [logging.FileHandler(args.output_dir / "triage.log")]
    if args.verbose:
        handlers.append(logging.StreamHandler())
    # Root stays at WARNING so third-party libraries (matplotlib's font-manager
    # in particular) don't flood the log file; only this package's own logger
    # is raised to INFO/DEBUG. An earlier version set the root logger itself
    # to DEBUG under -v, which pulled in ~900 lines of matplotlib font-cache
    # debug output for a single run.
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )
    logging.getLogger("triage").setLevel(logging.DEBUG if args.verbose else logging.INFO)

    console = Console()
    now = datetime.now()

    tickets = report.load_tickets(args.input)
    tickets = report.triage_all(tickets, now=now)
    summary = report.summarize(tickets)

    report.render_console_report(tickets, summary, console)

    csv_out = args.output_dir / "tickets_triaged.csv"
    report.export_csv(tickets, csv_out)
    console.print(f"\nTriaged export written to [bold]{csv_out}[/bold]")

    if not args.no_charts:
        for path in report.generate_charts(summary, args.output_dir):
            console.print(f"Chart written to [bold]{path}[/bold]")

    console.print(f"Log written to [bold]{args.output_dir / 'triage.log'}[/bold]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
