from datetime import date
from pathlib import Path

from cfptracker import storage
from cfptracker.models import Status, Submission, Talk


def test_slugify():
    assert storage.slugify("BSides Madison 2026!") == "bsides-madison-2026"


def test_unique_id_avoids_collision():
    state = storage.State(
        submissions=[Submission(id="bsides", conference="BSides", cfp_deadline=date(2026, 8, 1))]
    )
    assert storage.unique_id(state, "bsides") == "bsides-2"


def test_save_and_load_roundtrip(tmp_path: Path):
    state = storage.State(
        talks=[Talk(title="My Talk", versions=["v1", "v2"])],
        submissions=[
            Submission(
                id="bsides",
                conference="BSides Madison",
                cfp_deadline=date(2026, 8, 1),
                talk_title="My Talk",
                talk_version="v1",
                status=Status.SUBMITTED,
                submitted_date=date(2026, 7, 1),
            )
        ],
    )
    path = tmp_path / "state.json"
    storage.save_state(path, state)
    loaded = storage.load_state(path)

    assert loaded.talks[0].title == "My Talk"
    assert loaded.submissions[0].status == Status.SUBMITTED
    assert loaded.submissions[0].submitted_date == date(2026, 7, 1)


def test_load_missing_file_returns_empty_state(tmp_path: Path):
    state = storage.load_state(tmp_path / "does_not_exist.json")
    assert state.talks == []
    assert state.submissions == []
