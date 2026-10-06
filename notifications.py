import httpx

from connections import get_ntf_connection
from custom_logging import get_custom_logger
from db.connection import get_db_connection

logger = get_custom_logger('Notifications')


def send_notification(topic, message):
    ntf_url = f'{get_ntf_connection(topic)}{message}'
    httpx.get(ntf_url, timeout=10)
    logger.info(f'Notification: {message}')


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
            logger.info(f'Notification saved: {message}')
