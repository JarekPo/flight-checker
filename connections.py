import os

from dotenv import load_dotenv

load_dotenv()
PROVIDER_API = os.getenv('HARP_API_BASE_URL')

NTF_BASE_URL = os.getenv('NTF_BASE_URL')
TOPIC_NAME = os.getenv('TOPIC_NAME')


def get_ntf_connection():
    return f'{NTF_BASE_URL}{TOPIC_NAME}/publish?message='
