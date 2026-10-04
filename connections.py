import os

from dotenv import load_dotenv

load_dotenv()
PROVIDER_API = os.getenv('HARP_API_BASE_URL')
NTF_BASE_URL = os.getenv('NTF_BASE_URL')


def get_ntf_connection(topic):
    return f'{NTF_BASE_URL}{topic}/publish?message='
