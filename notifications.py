from urllib.parse import quote

import httpx

from connections import get_ntf_connection
from custom_logging import get_custom_logger
from db.connection import get_db_connection

logger = get_custom_logger('Notifications')


def send_notification(topic, message):
    ntf_url = f'{get_ntf_connection(topic)}{quote(message, safe="")}'
    response = httpx.get(ntf_url, timeout=10)
    response.raise_for_status()
    logger.info('Notification sent: %s', message)


def save_notification(topic, message, script_name):
    query = """
    INSERT INTO notifications (topic, message, script_name)
    VALUES (%(topic)s, %(message)s, %(script_name)s)
    """

    params = {'topic': topic, 'message': message, 'script_name': script_name}

    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(query, params=params)
    logger.info('Notification saved: %s', message)
