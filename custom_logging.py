import logging
import logging.config
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent / 'app.log'

logging.config.dictConfig(
    {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s %(levelname)s %(name)s: %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': logging.INFO,
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'level': logging.INFO,
                'filename': str(LOG_FILE),
                'maxBytes': 5_000_000,
                'backupCount': 5,
            },
        },
        'loggers': {
            'app_logger': {
                'handlers': ['console', 'file'],
                'level': logging.INFO,
                'propagate': False,
            }
        },
    }
)


def get_custom_logger(script_name: str) -> logging.Logger:
    return logging.getLogger(f'app_logger.{script_name}')
