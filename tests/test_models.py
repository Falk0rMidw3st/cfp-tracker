from datetime import date

from cfptracker.models import Status, Submission


def test_days_until_deadline():
    sub = Submission(id="x", conference="Test Con", cfp_deadline=date(2026, 8, 1))
    assert sub.days_until_deadline(date(2026, 7, 15)) == 17


def test_is_open_for_watching_and_drafted_only():
    watching = Submission(id="a", conference="A", cfp_deadline=date(2026, 8, 1), status=Status.WATCHING)
    drafted = Submission(id="b", conference="B", cfp_deadline=date(2026, 8, 1), status=Status.DRAFTED)
    submitted = Submission(id="c", conference="C", cfp_deadline=date(2026, 8, 1), status=Status.SUBMITTED)

    assert watching.is_open()
    assert drafted.is_open()
    assert not submitted.is_open()
