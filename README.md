# Python Projects

[![CI](https://github.com/malikautomates/python-projects/actions/workflows/ci.yml/badge.svg)](https://github.com/malikautomates/python-projects/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A collection of standalone Python tools, each built and documented as
operational work rather than a tutorial exercise: the problem it solves, the
design decisions behind it, a real test suite, and verification evidence —
actual captures of the tool running, not mockups.

---

## Project index

| # | Project | Summary | Skills demonstrated | Status |
|---|---|---|---|---|
| 01 | [Helpdesk Ticket Triage Toolkit](01-helpdesk-ticket-triage-toolkit/) | Categorizes, prioritizes, and SLA-checks helpdesk tickets from a CSV export; console report, CSV export, and charts | CLI tooling (argparse), rule-based logic, pytest, Rich, Matplotlib, logging | Complete |

Status values: `Planned` · `In progress` · `Complete`

---

## Conventions used throughout this repository

**Every project states its rationale.** Design decisions are documented, not
just implemented — see each project's own `docs/design-notes.md`.

**Every project ships with a real test suite**, run on every push by
[GitHub Actions](.github/workflows/ci.yml) against Python 3.11 and 3.13,
together with an end-to-end run of the tool against its sample data.

**Every README's screenshots are real captures**, regenerated from a live run
by a script committed alongside the code (`scripts/capture_*.py` in each
project) — so the documentation can't silently drift out of sync with the
code it describes.

**Limitations are documented, not hidden.** Where a tool has a real blind
spot, it's named directly with a worked example, not smoothed over.

---

## Contact

- **Email:** [m.abdulmaliksani008@gmail.com](mailto:m.abdulmaliksani008@gmail.com)
- **LinkedIn:** [linkedin.com/in/muhammed-abdulmalik-a84131267](https://www.linkedin.com/in/muhammed-abdulmalik-a84131267)
- **GitHub:** [malikautomates](https://github.com/malikautomates)

Released under the [MIT License](LICENSE).
