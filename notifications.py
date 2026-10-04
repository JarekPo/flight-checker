import httpx

from connections import get_ntf_connection
from db.connection import get_db_connection


def send_notification(topic, message):
    ntf_url = f'{get_ntf_connection(topic)}{message}'
    httpx.get(ntf_url, timeout=10)
    print(f'Notification: {message}')


def save_notification(topic, message, script_name):

    query = """
    INSERT INTO notifications (topic, message, script_name)
    VALUES (%(topic)s, %(message)s, %(script_name)s)
    ON CONFLICT (topic, message) DO NOTHING
    RETURNING id
    """

    params = {'topic': topic, 'message': message, 'script_name': script_name}

    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(query, params=params)
        result = cur.fetchone()
        if result is not None:
            print(f'Notification saved: {message}')
