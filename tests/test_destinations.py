import pytest

from destinations import diff_destinations


@pytest.mark.parametrize(
    ('api', 'db', 'new', 'removed'),
    [
        (['DUB', 'STN'], ['STN', 'BCN'], {'DUB'}, {'BCN'}),
        (['DUB'], ['DUB'], set(), set()),
        ([], ['DUB'], set(), {'DUB'}),
    ],
)
def test_diff_destinations(api, db, new, removed):
    assert diff_destinations(api, db) == (new, removed)
