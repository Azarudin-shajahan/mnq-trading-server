"""Decision-log (htf_journal) grade-field tests.

The hardened cockpit plan needs each forward decision to record the GRADE the
playbook/cockpit assigned, so grades can later be EARNED (yellow -> green) from
forward outcomes. These tests pin the schema + round-trip, no heavy data deps.
"""
import csv
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "diagnostics"))
import htf_outcomes as O  # noqa: E402


def test_playbook_grade_in_schema():
    assert "playbook_grade" in O.ALL_FIELDS, "decision log must carry the playbook grade"


def test_playbook_grade_after_human_fields():
    # grade is a forward-only human-context field: it should sit with the human block,
    # before the auto-filled v8.18/outcome columns.
    gi = O.ALL_FIELDS.index("playbook_grade")
    assert gi > O.ALL_FIELDS.index("human_override")
    assert gi < O.ALL_FIELDS.index("actual_dir")


def test_forward_row_roundtrips_grade():
    row = {f: "" for f in O.ALL_FIELDS}
    row.update(date="2026-06-25", split="forward", human_bias="long",
               human_override="take", playbook_grade="green")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=O.ALL_FIELDS)
    w.writeheader()
    w.writerow(row)
    back = next(csv.DictReader(io.StringIO(buf.getvalue())))
    assert back["playbook_grade"] == "green"
    assert back["human_override"] == "take"


def test_backfill_row_has_blank_grade():
    # historical backfill rows must leave the grade blank (forward-only, like human labels)
    row = {f: "" for f in O.ALL_FIELDS}
    row.update(date="2022-03-01", split="backfill")
    assert row["playbook_grade"] == ""
