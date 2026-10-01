import os

from dotenv import load_dotenv

load_dotenv()
PROVIDER_API = os.getenv('HARP_API_BASE_URL')
