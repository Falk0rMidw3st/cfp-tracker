from __future__ import annotations

from .storage import State


def render_markdown(state: State) -> str:
    lines = ["# CFP Tracker", ""]

    if state.talks:
        lines.append("## Talks")
        for t in state.talks:
            lines.append(f"- **{t.title}** — versions: {', '.join(t.versions) or 'none'}")
        lines.append("")

    lines.append("## Submissions")
    for s in sorted(state.submissions, key=lambda s: s.cfp_deadline):
        talk_label = f" ({s.talk_title} / {s.talk_version})" if s.talk_title else ""
        lines.append(f"- **{s.conference}** — deadline {s.cfp_deadline.isoformat()} — {s.status.value}{talk_label}")

    return "\n".join(lines)
