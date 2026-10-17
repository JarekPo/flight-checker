import datetime
from typing import LiteralString

from arg_registry_app import ArgRegistryApp
from db.connection import get_db_connection
from notifications import save_notification, send_notification
from provider_api import get_availabilities

SAVE_QUERIES: dict[str, LiteralString] = {
    'insert': """
        INSERT INTO availabilities (from_airport, to_airport, last_date)
        VALUES (%(from_airport)s, %(to_airport)s, %(last_date)s)
        RETURNING last_date
    """,
    'update': """
        UPDATE availabilities
        SET last_date = %(last_date)s
        WHERE from_airport = %(from_airport)s
        AND to_airport = %(to_airport)s
        RETURNING last_date
    """,
}


def decide_action(current_last_date, api_last_date):
    if api_last_date is None:
        return None
    if current_last_date is None:
        return 'insert'
    if api_last_date > current_last_date:
        return 'update'
    return None


class Availabilities(ArgRegistryApp):
    use_args = ('from-airport', 'to-airport', 'topic')

    def get_last_date(self, params):
        query = """
        SELECT last_date
        FROM availabilities
        WHERE from_airport = %(from_airport)s AND to_airport = %(to_airport)s
        """
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(query, params=params)
            return cur.fetchone()

    def main(self):
        from_airport = self.args.from_airport
        to_airport = self.args.to_airport
        topic = self.args.topic
        route = f'{from_airport} to {to_airport}'
        params = {'from_airport': from_airport, 'to_airport': to_airport}

        row = self.get_last_date(params)
        current_last_date = row['last_date'] if row is not None else None

        api_dates = get_availabilities(from_airport, to_airport)
        api_last_date_string = max(api_dates or [], default=None)
        api_last_date = datetime.date.fromisoformat(api_last_date_string) if api_last_date_string else None

        action = decide_action(current_last_date, api_last_date)
        if action is None:
            self.logger.info(f'No new availability for {route}')
            return

        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(SAVE_QUERIES[action], params={**params, 'last_date': api_last_date})
            saved = cur.fetchone()
        if saved is None:
            self.logger.error(f'Database did not return a row after {action} for {route}')
            return

        self.logger.info(f'Saved last_date for {route} ({action}): {saved["last_date"]}')
        message = f'New availability found for {route}: {current_last_date} -> {saved["last_date"]}'
        send_notification(topic, message)
        save_notification(topic, message, self.__class__.__name__)


if __name__ == '__main__':
    with Availabilities() as app:
        app.run()
