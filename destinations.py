import httpx

from baseApp import BaseApp
from connections import PROVIDER_API
from db.connection import get_db_connection
from notifications import save_notification, send_notification


class Destinations(BaseApp):
    def add_args(self):
        parser = super().add_args()
        parser.add_argument(
            '--from_a',
            required=True,
            help='Departure airport IATA code',
        )
        parser.add_argument(
            '--topic',
            required=True,
            help='Notification topic',
        )
        return parser

    def get_destinations(self, airport_code):
        destinations = httpx.get(
            f'{PROVIDER_API}api/views/locate/searchWidget/routes/en/airport/{airport_code}', timeout=10
        )
        if destinations.status_code == 200:
            return destinations.json()
        return None

    def list_destinations(self, airport_code):
        query = """
        SELECT to_airport
        FROM destinations
        WHERE from_airport = %(airport_code)s
        AND is_active = true
        """
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(query, params={'airport_code': airport_code})
            return [row['to_airport'] for row in cur.fetchall()]

    def main(self):
        from_airport = self.args.from_a
        topic = self.args.topic
        api_destinations = self.get_destinations(from_airport)
        if api_destinations is None:
            self.logger.error(f'Failed to fetch destinations for {from_airport}, skipping')
            return

        destinations = [dest['arrivalAirport']['code'] for dest in api_destinations]
        db_destinations = self.list_destinations(from_airport)
        new_destinations = set(destinations) - set(db_destinations)
        removed_destinations = set(db_destinations) - set(destinations)
        if new_destinations:
            self.logger.info(f'New destinations found for {from_airport}: {new_destinations}')
            with get_db_connection() as conn, conn.cursor() as cur:
                for dest in new_destinations:
                    cur.execute(
                        """
                        INSERT INTO destinations (from_airport, to_airport)
                        VALUES (%(from_airport)s, %(to_airport)s)
                        ON CONFLICT (from_airport, to_airport) WHERE is_active DO NOTHING
                        """,
                        params={'from_airport': from_airport, 'to_airport': dest},
                    )
            message = f'New destinations found for {from_airport}: {new_destinations}'
            self.logger.info(f'Sending notification for {from_airport}: {message}')
            send_notification(topic, message)
            save_notification(topic, message, self.__class__.__name__)
        if removed_destinations:
            self.logger.info(f'Removed destinations for {from_airport}: {removed_destinations}')
            with get_db_connection() as conn, conn.cursor() as cur:
                for dest in removed_destinations:
                    cur.execute(
                        """
                        UPDATE destinations
                        SET is_active = false, updated_at = now()
                        WHERE from_airport = %(from_airport)s
                        AND to_airport = %(to_airport)s
                        AND is_active
                        """,
                        params={'from_airport': from_airport, 'to_airport': dest},
                    )
            message = f'Removed destinations for {from_airport}: {removed_destinations}'
            send_notification(topic, message)
            save_notification(topic, message, self.__class__.__name__)


if __name__ == '__main__':
    with Destinations() as app:
        app.run()
