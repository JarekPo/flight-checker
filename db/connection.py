import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import DictRow, dict_row

load_dotenv()

DB_URL = os.getenv('DB_URL')


def get_db_connection() -> psycopg.Connection[DictRow]:
    if DB_URL is None:
        raise RuntimeError('DB_URL environment variable is not set')
    return psycopg.Connection[DictRow].connect(
        conninfo=DB_URL,
        row_factory=dict_row,
    )
