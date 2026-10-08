from arg_registry_app import ArgRegistryApp
from db.connection import get_db_connection
from notifications import save_notification, send_notification
from provider_api import get_destinations


class Destinations(ArgRegistryApp):
    use_args = ('from-airport', 'topic')

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
        from_airport = self.args.from_airport
        topic = self.args.topic
        api_destinations = get_destinations(from_airport)
        if api_destinations is None:
            self.logger.error('Failed to fetch destinations for %s, skipping', from_airport)
            return

        destinations = [dest['arrivalAirport']['code'] for dest in api_destinations]
        db_destinations = self.list_destinations(from_airport)
        new_destinations = set(destinations) - set(db_destinations)
        removed_destinations = set(db_destinations) - set(destinations)
        if new_destinations:
            self.logger.info('New destinations found for %s: %s', from_airport, new_destinations)
            with get_db_connection() as conn, conn.cursor() as cur:
                for dest in new_destinations:
                    cur.execute(
                        """
                        INSERT INTO destinations (from_airport, to_airport)
                        VALUES (%(from_airport)s, %(to_airport)s)
                        ON CONFLICT (from_airport, to_airport)
                        DO UPDATE SET is_active = true, updated_at = now()
                        """,
                        params={'from_airport': from_airport, 'to_airport': dest},
                    )
            message = f'New destinations found for {from_airport}: {new_destinations}'
            self.logger.info('Sending notification for %s: %s', from_airport, message)
            send_notification(topic, message)
            save_notification(topic, message, self.__class__.__name__)
        if removed_destinations:
            self.logger.info('Removed destinations for %s: %s', from_airport, removed_destinations)
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
