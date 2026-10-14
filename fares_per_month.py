import datetime
import statistics
from decimal import Decimal

from arg_registry_app import ArgRegistryApp
from db.connection import get_db_connection
from notifications import save_notification, send_notification
from provider_api import get_availabilities, get_one_way_fares


class FaresPerMonth(ArgRegistryApp):
    use_args = ('from-airport', 'to-airport', 'topic')

    def get_last_fares(self, month, from_airport, to_airport):
        query = """
        SELECT *
        FROM fares_in_month
        WHERE from_airport = %(from_airport)s
        AND to_airport = %(to_airport)s
        AND month = %(month)s
        ORDER BY inserted_at DESC
        LIMIT 1;
        """
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(query, params={'from_airport': from_airport, 'to_airport': to_airport, 'month': month})
            return cur.fetchall()

    def get_available_months(self, from_airport, to_airport):
        dates = get_availabilities(from_airport, to_airport)
        if not dates:
            return []
        month_end = datetime.date.fromisoformat(dates[-1])

        months = []
        month_start = (datetime.date.today().replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
        while month_start <= month_end:
            months.append(month_start)
            month_start = (month_start + datetime.timedelta(days=32)).replace(day=1)
        return months

    def check_fares(self, last_fares, one_way_fares):
        fare_metrics = ['min_fare', 'max_fare', 'avg_fare', 'median_fare']
        fares: dict[str, Decimal] = dict.fromkeys(fare_metrics, Decimal(0))
        cheaper_fares = []
        if not one_way_fares:
            return fares, cheaper_fares, None
        outbound = one_way_fares['outbound']
        currency = outbound['minFare']['price']['currencyCode']
        fares['min_fare'] = outbound['minFare']['price']['value']
        fares['max_fare'] = outbound['maxFare']['price']['value']
        agg_prices = [Decimal(fare['price']['value']) for fare in outbound['fares'] if fare['arrivalDate'] is not None]
        fares['avg_fare'] = round(statistics.mean(agg_prices), 2)
        fares['median_fare'] = round(statistics.median(agg_prices), 2)

        if not last_fares:
            return fares, fare_metrics, currency

        cheaper_fares.extend(metric for metric in fare_metrics if last_fares[0][metric] > fares[metric])
        return fares, cheaper_fares, currency

    def main(self):
        from_airport = self.args.from_airport
        to_airport = self.args.to_airport
        topic = self.args.topic
        months = self.get_available_months(from_airport, to_airport)
        for month in months:
            last_fares = self.get_last_fares(month, from_airport, to_airport)
            one_way_fares = get_one_way_fares(month, from_airport, to_airport)
            fares, cheaper_fares, currency = self.check_fares(last_fares, one_way_fares)
            if cheaper_fares:
                mapped_fares = {metric: fares[metric] for metric in cheaper_fares}
                with get_db_connection() as conn, conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO fares_in_month (from_airport, to_airport, month, currency, min_fare, max_fare, avg_fare, median_fare, inserted_at)
                        VALUES (%(from_airport)s, %(to_airport)s, %(month)s, %(currency)s, %(min_fare)s, %(max_fare)s, %(avg_fare)s, %(median_fare)s, now())
                        """,
                        params={
                            'from_airport': from_airport,
                            'to_airport': to_airport,
                            'month': month,
                            'currency': currency,
                            'min_fare': fares['min_fare'],
                            'max_fare': fares['max_fare'],
                            'avg_fare': fares['avg_fare'],
                            'median_fare': fares['median_fare'],
                        },
                    )
                fares_text = ', '.join(f"'{key}': {value:.2f}" for key, value in mapped_fares.items())
                message = f'New cheaper fares found for {from_airport} to {to_airport} in month {month}: {fares_text}'
                send_notification(topic, message)
                save_notification(topic, message, self.__class__.__name__)


if __name__ == '__main__':
    with FaresPerMonth() as app:
        app.run()
