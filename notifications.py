import httpx

from connections import get_ntf_connection


def send_notification(message):
    ntf_url = f'{get_ntf_connection()}{message}'
    httpx.get(ntf_url, timeout=10)
    print(f'Notification: {message}')
    print(f'Notification sent to {ntf_url}')
