from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from . import storage
from .models import Status, Submission, Talk

console = Console()

DEFAULT_STATE_FILE = Path("cfp_state.json")


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


@click.group()
@click.option(
    "--state-file",
    type=click.Path(path_type=Path),
    default=DEFAULT_STATE_FILE,
    show_default=True,
    help="Path to the JSON state file.",
)
@click.pass_context
def main(ctx: click.Context, state_file: Path) -> None:
    """CFP Tracker: track conference submissions, deadlines, and decisions."""
    ctx.ensure_object(dict)
    ctx.obj["state_file"] = state_file


@main.group()
def talk() -> None:
    """Manage talk titles and versions."""


@talk.command(name="add")
@click.argument("title")
@click.option("--version", "version_name", required=True, help="Version/variant name for this talk.")
@click.pass_context
def talk_add(ctx: click.Context, title: str, version_name: str) -> None:
    """Register a talk title, or add a version to an existing one."""
    state_file: Path = ctx.obj["state_file"]
    state = storage.load_state(state_file)
    existing = next((t for t in state.talks if t.title == title), None)
    if existing is None:
        existing = Talk(title=title, versions=[])
        state.talks.append(existing)
    if version_name not in existing.versions:
        existing.versions.append(version_name)
    storage.save_state(state_file, state)
    console.print(f"[green]OK[/] '{title}' now has versions: {', '.join(existing.versions)}")


@talk.command(name="list")
@click.pass_context
def talk_list(ctx: click.Context) -> None:
    """List registered talks and their versions."""
    state = storage.load_state(ctx.obj["state_file"])
    table = Table(title="Talks")
    table.add_column("Title")
    table.add_column("Versions")
    for t in state.talks:
        table.add_row(t.title, ", ".join(t.versions) or "-")
    console.print(table)


@main.command()
@click.option("--conference", required=True, help="Conference name.")
@click.option("--deadline", "deadline_str", required=True, help="CFP deadline, YYYY-MM-DD.")
@click.option("--event-date", "event_date_str", default=None, help="Event start date, YYYY-MM-DD.")
@click.option("--talk", "talk_title", default=None, help="Talk title (must be registered first).")
@click.option("--version", "talk_version", default=None, help="Talk version submitted.")
@click.option("--url", default="", help="CFP submission URL.")
@click.option("--notes", default="", help="Free-text notes.")
@click.option(
    "--status",
    "status_str",
    type=click.Choice([s.value for s in Status]),
    default=Status.WATCHING.value,
    help="Initial status.",
)
@click.pass_context
def add(
    ctx: click.Context,
    conference: str,
    deadline_str: str,
    event_date_str: Optional[str],
    talk_title: Optional[str],
    talk_version: Optional[str],
    url: str,
    notes: str,
    status_str: str,
) -> None:
    """Track a new CFP / submission."""
    state_file: Path = ctx.obj["state_file"]
    state = storage.load_state(state_file)

    if talk_title and not any(t.title == talk_title for t in state.talks):
        raise click.ClickException(f"Unknown talk '{talk_title}'. Register it with 'cfp talk add' first.")

    sub_id = storage.unique_id(state, storage.slugify(conference))
    submission = Submission(
        id=sub_id,
        conference=conference,
        cfp_deadline=_parse_date(deadline_str),
        event_date=_parse_date(event_date_str) if event_date_str else None,
        talk_title=talk_title,
        talk_version=talk_version,
        status=Status(status_str),
        url=url,
        notes=notes,
    )
    state.submissions.append(submission)
    storage.save_state(state_file, state)
    console.print(f"[green]Added[/] {sub_id} ({conference}, deadline {submission.cfp_deadline.isoformat()})")


@main.command(name="status")
@click.argument("submission_id")
@click.argument("new_status", type=click.Choice([s.value for s in Status]))
@click.option("--date", "date_str", default=None, help="Date of this status change, YYYY-MM-DD (default: today).")
@click.pass_context
def set_status(ctx: click.Context, submission_id: str, new_status: str, date_str: Optional[str]) -> None:
    """Update a submission's status (submitted / accepted / rejected / withdrawn)."""
    state_file: Path = ctx.obj["state_file"]
    state = storage.load_state(state_file)
    submission = next((s for s in state.submissions if s.id == submission_id), None)
    if submission is None:
        raise click.ClickException(f"No submission with id '{submission_id}'.")

    when = _parse_date(date_str) if date_str else date.today()
    submission.status = Status(new_status)
    if submission.status == Status.SUBMITTED:
        submission.submitted_date = when
    elif submission.status in (Status.ACCEPTED, Status.REJECTED):
        submission.decision_date = when

    storage.save_state(state_file, state)
    console.print(f"[green]{submission_id}[/] -> {new_status}")


@main.command(name="list")
@click.option("--status", "status_filter", type=click.Choice([s.value for s in Status]), default=None)
@click.option("--open", "open_only", is_flag=True, help="Only watching/drafted (not yet submitted).")
@click.pass_context
def list_submissions(ctx: click.Context, status_filter: Optional[str], open_only: bool) -> None:
    """List tracked submissions."""
    state = storage.load_state(ctx.obj["state_file"])
    items = state.submissions
    if status_filter:
        items = [s for s in items if s.status.value == status_filter]
    if open_only:
        items = [s for s in items if s.is_open()]
    items = sorted(items, key=lambda s: s.cfp_deadline)

    table = Table(title="CFP Submissions")
    table.add_column("ID")
    table.add_column("Conference")
    table.add_column("Deadline")
    table.add_column("Status")
    table.add_column("Talk")

    for s in items:
        talk_label = f"{s.talk_title} ({s.talk_version})" if s.talk_title else "-"
        table.add_row(s.id, s.conference, s.cfp_deadline.isoformat(), s.status.value, talk_label)
    console.print(table)


@main.command()
@click.option("--month", "month_str", default=None, help="Month to check, YYYY-MM (default: current month).")
@click.pass_context
def due(ctx: click.Context, month_str: Optional[str]) -> None:
    """Show what's due this month: open CFPs deadlined in the target month, plus anything overdue."""
    state = storage.load_state(ctx.obj["state_file"])
    today = date.today()
    if month_str:
        year, month = (int(part) for part in month_str.split("-"))
    else:
        year, month = today.year, today.month

    open_items = [s for s in state.submissions if s.is_open()]
    targeted = [
        s
        for s in open_items
        if s.cfp_deadline < today or (s.cfp_deadline.year == year and s.cfp_deadline.month == month)
    ]
    targeted.sort(key=lambda s: s.cfp_deadline)

    table = Table(title=f"Due in {year}-{month:02d}")
    table.add_column("Days")
    table.add_column("Deadline")
    table.add_column("Conference")
    table.add_column("Status")
    table.add_column("Talk")

    overdue_count = 0
    for s in targeted:
        days = (s.cfp_deadline - today).days
        if days < 0:
            overdue_count += 1
            days_str = f"[bold red]{days} (OVERDUE)[/]"
        elif days <= 7:
            days_str = f"[yellow]{days}[/]"
        else:
            days_str = str(days)
        talk_label = f"{s.talk_title} ({s.talk_version})" if s.talk_title else "-"
        table.add_row(days_str, s.cfp_deadline.isoformat(), s.conference, s.status.value, talk_label)

    console.print(table)
    console.print(f"\n{len(targeted)} open, {overdue_count} overdue")


@main.command()
@click.option("--output", type=click.Path(path_type=Path), default=None, help="Output file (default: stdout).")
@click.pass_context
def export(ctx: click.Context, output: Optional[Path]) -> None:
    """Export a Markdown summary of all tracked submissions."""
    from .export import render_markdown

    state = storage.load_state(ctx.obj["state_file"])
    doc = render_markdown(state)
    if output:
        output.write_text(doc, encoding="utf-8")
        console.print(f"[green]Exported[/] -> {output}")
    else:
        console.print(doc)


if __name__ == "__main__":
    main()
