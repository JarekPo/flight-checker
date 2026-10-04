import datetime

import httpx

from baseApp import BaseApp
from connections import PROVIDER_API
from db.connection import get_db_connection
from notifications import send_notification

update_query = """
UPDATE availabilities
SET last_date = %(last_date)s
WHERE from_airport = %(from_airport)s AND to_airport = %(to_airport)s
"""


class Availabilities(BaseApp):
    def add_args(self):
        parser = super().add_args()
        parser.add_argument(
            '--from_a',
            required=True,
            help='Departure airport IATA code',
        )

        parser.add_argument(
            '--to_a',
            required=True,
            help='Arrival airport IATA code',
        )
        return parser

    def get_last_date(self, params):
        query = """
        SELECT last_date
        FROM availabilities
        WHERE from_airport = %(from_airport)s AND to_airport = %(to_airport)s
        """

        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(query, params=params)
            return cur.fetchone()

    def get_availabilities(self, departure_airport, arrival_airport):
        availabilities = httpx.get(
            f'{PROVIDER_API}api/farfnd/3/oneWayFares/{departure_airport}/{arrival_airport}/availabilities', timeout=10
        )
        if availabilities.status_code == 200:
            return availabilities.json()
        return None

    def main(self):
        # args = self.add_args
        from_airport = self.args.from_a
        to_airport = self.args.to_a
        params = {'from_airport': from_airport, 'to_airport': to_airport}
        result = self.get_last_date(params)
        current_last_date = result['last_date'] if result is not None else None

        api_availabilities = self.get_availabilities(from_airport, to_airport)

        api_last_date_string = api_availabilities[-10] if api_availabilities else None

        api_last_date = datetime.date.fromisoformat(api_last_date_string) if api_last_date_string else None

        update_params = {
            'from_airport': from_airport,
            'to_airport': to_airport,
            'last_date': api_last_date,
        }

        if current_last_date and api_last_date and current_last_date < api_last_date:
            with get_db_connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE availabilities
                    SET last_date = %(last_date)s
                    WHERE from_airport = %(from_airport)s
                    AND to_airport = %(to_airport)s
                    RETURNING last_date
                    """,
                    params=update_params,
                )
                result = cur.fetchone()
                if result is not None:
                    print('Updated last_date:', result['last_date'])
                    send_notification(
                        f'New availability found for {from_airport} to {to_airport}: {result["last_date"]}'
                    )


if __name__ == '__main__':
    with Availabilities() as app:
        app.run()
