from decimal import Decimal
from typing import Any

import httpx

import provider_api
from fares_per_month import FaresPerMonth


def make_payload(min_price, max_price, prices):
    return {
        'outbound': {
            'minFare': {'price': {'value': min_price, 'currencyCode': 'EUR'}},
            'maxFare': {'price': {'value': max_price, 'currencyCode': 'EUR'}},
            'fares': [{'arrivalDate': '2026-11-02', 'price': {'value': p}} for p in prices],
        }
    }


def test_same_prices_are_not_cheaper():
    payload = make_payload(Decimal('100.00'), Decimal('300.00'), [Decimal('100.00'), Decimal('300.00')])
    last = [
        {
            'min_fare': Decimal('100.00'),
            'max_fare': Decimal('300.00'),
            'avg_fare': Decimal('200.00'),
            'median_fare': Decimal('200.00'),
        }
    ]
    _, cheaper, _ = FaresPerMonth().check_fares(last, payload)
    assert cheaper == []


def test_lower_prices_are_cheaper():
    payload = make_payload(Decimal('90.00'), Decimal('120.00'), [Decimal('90.00'), Decimal('120.00')])
    last = [
        {
            'min_fare': Decimal('100.00'),
            'max_fare': Decimal('300.00'),
            'avg_fare': Decimal('200.00'),
            'median_fare': Decimal('200.00'),
        }
    ]
    _, cheaper, _ = FaresPerMonth().check_fares(last, payload)
    assert cheaper == ['min_fare', 'max_fare', 'avg_fare', 'median_fare']


def test_dearer_prices_are_not_cheaper():
    payload = make_payload(Decimal('120.00'), Decimal('310.00'), [Decimal('210.00'), Decimal('210.00')])
    last = [
        {
            'min_fare': Decimal('100.00'),
            'max_fare': Decimal('300.00'),
            'avg_fare': Decimal('200.00'),
            'median_fare': Decimal('200.00'),
        }
    ]
    _, cheaper, _ = FaresPerMonth().check_fares(last, payload)
    assert cheaper == []


def test_report_only_fares_that_dropped():
    payload = make_payload(Decimal('80.00'), Decimal('300.00'), [Decimal('190.00'), Decimal('200.00')])
    last = [
        {
            'min_fare': Decimal('100.00'),
            'max_fare': Decimal('300.00'),
            'avg_fare': Decimal('200.00'),
            'median_fare': Decimal('200.00'),
        }
    ]
    _, cheaper, _ = FaresPerMonth().check_fares(last, payload)
    assert cheaper == ['min_fare', 'avg_fare', 'median_fare']

    payload2 = make_payload(Decimal('100.00'), Decimal('275.00'), [Decimal('200.00'), Decimal('200.00')])
    last2 = [
        {
            'min_fare': Decimal('100.00'),
            'max_fare': Decimal('300.00'),
            'avg_fare': Decimal('200.00'),
            'median_fare': Decimal('200.00'),
        }
    ]
    _, cheaper2, _ = FaresPerMonth().check_fares(last2, payload2)
    assert cheaper2 == ['max_fare']


def test_no_previous_fares_reports_all_metrics():
    payload = make_payload(Decimal('120.00'), Decimal('310.00'), [Decimal('210.00'), Decimal('210.00')])
    last = []
    _, cheaper, _ = FaresPerMonth().check_fares(last, payload)
    assert cheaper == ['min_fare', 'max_fare', 'avg_fare', 'median_fare']


def test_no_prices_are_not_cheaper():
    last = [
        {
            'min_fare': Decimal('100.00'),
            'max_fare': Decimal('300.00'),
            'avg_fare': Decimal('200.00'),
            'median_fare': Decimal('200.00'),
        }
    ]
    _, cheaper, currency = FaresPerMonth().check_fares(last, None)
    assert cheaper == []
    assert currency is None


def test_get_one_way_fares_returns_decimals(monkeypatch):
    body = b'{"outbound": {"minFare": {"price": {"value": 132.19}}}}'
    monkeypatch.setattr(httpx, 'get', lambda *args, **kwargs: httpx.Response(200, content=body))

    result: Any = provider_api.get_one_way_fares('2026-11-01', 'LTN', 'DUB')

    assert result['outbound']['minFare']['price']['value'] == Decimal('132.19')


def test_get_one_way_fares_returns_none_on_server_error(monkeypatch):
    monkeypatch.setattr(httpx, 'get', lambda *args, **kwargs: httpx.Response(500))
    assert provider_api.get_one_way_fares('2026-11-01', 'LTN', 'DUB') is None
