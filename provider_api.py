from decimal import Decimal

import httpx

from connections import PROVIDER_API


def get_availabilities(from_airport, to_airport):
    response = httpx.get(
        f'{PROVIDER_API}api/farfnd/3/oneWayFares/{from_airport}/{to_airport}/availabilities',
        timeout=10,
    )
    if response.status_code == 200:
        return response.json()
    return None


def get_destinations(airport_code):
    destinations = httpx.get(
        f'{PROVIDER_API}api/views/locate/searchWidget/routes/en/airport/{airport_code}', timeout=10
    )
    if destinations.status_code == 200:
        return destinations.json()
    return None


def get_one_way_fares(month, from_airport, to_airport):
    response = httpx.get(
        f'{PROVIDER_API}api/farfnd/v4/oneWayFares/{from_airport}/{to_airport}/cheapestPerDay',
        params={'outboundMonthOfDate': month},
        timeout=10,
    )
    if response.status_code == 200:
        return response.json(parse_float=Decimal)
    return None
