import datetime

import pytest

from availabilities import decide_action

EARLIER = datetime.date(2026, 11, 1)
LATER = datetime.date(2026, 11, 2)


@pytest.mark.parametrize(
    ('current', 'api', 'expected'),
    [
        (None, None, None),  # nothing stored, API gave nothing
        (EARLIER, None, None),  # API gave nothing: keep what we have
        (None, EARLIER, 'insert'),  # route seen for the first time
        (EARLIER, LATER, 'update'),  # API reports a later date
        (LATER, LATER, None),  # unchanged
        (LATER, EARLIER, None),  # API date went backwards: ignored
    ],
)
def test_decide_action(current, api, expected):
    assert decide_action(current, api) == expected
