import os
from pathlib import Path
from typing import Dict, Set, List

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
END_DATA_DIR = BASE_DIR / 'end_data'
LOGS_DIR = BASE_DIR / 'logs'

# Create necessary directories
for directory in [DATA_DIR, END_DATA_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# File paths
FILE_PATHS = {
    'all_offers': DATA_DIR / 'all_offers.csv',
    'pancernik_empty': DATA_DIR / 'pancernik_empty_offers.csv',
    'bizon_empty': DATA_DIR / 'bizon_empty_offers.csv',
    'bewoodgrizz_empty': DATA_DIR / 'bewoodgrizz_empty_offers.csv',
    'all_offers_cleaned': END_DATA_DIR / 'all_offers_cleaned.xlsx',
    'all_offers_ready': END_DATA_DIR / 'all_offers_ready.xlsx',
    'pancernik_result': END_DATA_DIR / 'pancernik_empty_offers-result.xlsx',
    'bizon_result': END_DATA_DIR / 'bizon_empty_offers-result.xlsx',
    'bewoodgrizz_result': END_DATA_DIR / 'bewoodgrizz_empty_offers-result.xlsx',
}

# Google Sheets configuration
GOOGLE_SHEETS = {
    'url': 'https://docs.google.com/spreadsheets/d/1rz6QThoRfEreZWRczP0B8tuZoorVvSZlC7qWwryi-o0/export?format=csv&gid=0',
    'sheet_id': '1rz6QThoRfEreZWRczP0B8tuZoorVvSZlC7qWwryi-o0',
}

# HTML cleaning configuration
ALLOWED_TAGS: Set[str] = {
    'h2', 'h3', 'p', 'strong', 'em', 'img', 'hr', 'ul', 'ol', 'li', 
    'br', 'a', 'iframe', 'summary', 'details', 'section'
}

ALLOWED_ATTRS: Dict[str, List[str]] = {
    'img': ['src', 'alt'],
    'a': ['href', 'target'],
    'p': ['class', 'id'],
    'h2': ['class', 'id'],
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'app.log',
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

# Data processing configuration
CSV_DELIMITER = ';'
EXCLUDED_PRODUCTS = ['wydmuszka']
BETA_CLASS_SUFFIX = '-beta'

# Error messages
ERROR_MESSAGES = {
    'file_not_found': 'File not found or not accessible: {}',
    'invalid_html': 'Invalid HTML input',
    'google_sheets_error': 'Error reading Google Sheets data: {}',
    'processing_error': 'Error processing data: {}',
} 