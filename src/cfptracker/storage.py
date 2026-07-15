from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from .models import Status, Submission, Talk


@dataclass
class State:
    talks: list[Talk] = field(default_factory=list)
    submissions: list[Submission] = field(default_factory=list)


def save_state(path: Path, state: State) -> None:
    payload = {
        "talks": [asdict(t) for t in state.talks],
        "submissions": [
            {
                **asdict(s),
                "status": s.status.value,
                "cfp_deadline": s.cfp_deadline.isoformat(),
                "event_date": s.event_date.isoformat() if s.event_date else None,
                "submitted_date": s.submitted_date.isoformat() if s.submitted_date else None,
                "decision_date": s.decision_date.isoformat() if s.decision_date else None,
            }
            for s in state.submissions
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_state(path: Path) -> State:
    if not path.exists():
        return State()
    payload = json.loads(path.read_text(encoding="utf-8"))
    talks = [Talk(title=t["title"], versions=t.get("versions", [])) for t in payload.get("talks", [])]
    submissions = [
        Submission(
            id=s["id"],
            conference=s["conference"],
            cfp_deadline=date.fromisoformat(s["cfp_deadline"]),
            event_date=date.fromisoformat(s["event_date"]) if s.get("event_date") else None,
            talk_title=s.get("talk_title"),
            talk_version=s.get("talk_version"),
            status=Status(s.get("status", "watching")),
            url=s.get("url", ""),
            notes=s.get("notes", ""),
            submitted_date=date.fromisoformat(s["submitted_date"]) if s.get("submitted_date") else None,
            decision_date=date.fromisoformat(s["decision_date"]) if s.get("decision_date") else None,
        )
        for s in payload.get("submissions", [])
    ]
    return State(talks=talks, submissions=submissions)


def slugify(text: str) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in text)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def unique_id(state: State, base: str) -> str:
    existing = {s.id for s in state.submissions}
    candidate = base
    n = 2
    while candidate in existing:
        candidate = f"{base}-{n}"
        n += 1
    return candidate
