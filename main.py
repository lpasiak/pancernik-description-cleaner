import pandas as pd
import os
import logging
import logging.config
from pathlib import Path
from typing import Optional
from functions import clean_html, add_beta_classes
from compatibility import extract_h3_from_descriptions
from config import LOGGING_CONFIG, FILE_PATHS, CSV_DELIMITER, EXCLUDED_PRODUCTS

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

def validate_file_path(file_path: str) -> bool:
    """Validate if file exists and is accessible."""
    try:
        return os.path.isfile(file_path) and os.access(file_path, os.R_OK)
    except Exception as e:
        logger.error(f"Error validating file {file_path}: {str(e)}")
        return False

def safe_read_csv(file_path: str, delimiter: str = CSV_DELIMITER) -> Optional[pd.DataFrame]:
    """Safely read CSV file with error handling."""
    try:
        if not validate_file_path(file_path):
            raise FileNotFoundError(f"File not found or not accessible: {file_path}")
        return pd.read_csv(file_path, delimiter=delimiter)
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {str(e)}")
        return None

def safe_write_excel(df: pd.DataFrame, file_path: str) -> bool:
    """Safely write DataFrame to Excel with error handling."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_excel(file_path, index=False)
        logger.info(f"Successfully wrote data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing to Excel file {file_path}: {str(e)}")
        return False

def generate_clean_empty_descriptions():
    """Generate clean descriptions for empty offers from different vendors."""
    try:
        # Input files
        input_files = {
            'pancernik': FILE_PATHS['pancernik_empty'],
            'bizon': FILE_PATHS['bizon_empty'],
            'bewoodgrizz': FILE_PATHS['bewoodgrizz_empty']
        }
        
        # Output files
        output_files = {
            'pancernik': FILE_PATHS['pancernik_result'],
            'bizon': FILE_PATHS['bizon_result'],
            'bewoodgrizz': FILE_PATHS['bewoodgrizz_result']
        }

        for vendor, input_file in input_files.items():
            logger.info(f"Processing {vendor} data...")
            df = safe_read_csv(input_file)
            if df is None:
                continue

            # Process descriptions based on vendor
            if vendor == 'pancernik':
                df['new_description'] = df.apply(
                    lambda row: clean_html(row['Opis PL'], product_code=row['Seria']),
                    axis=1
                )
            elif vendor == 'bizon':
                df['new_description'] = df.apply(
                    lambda row: clean_html(row['Opis Shoper'], product_code=row['Seria - Kolor']),
                    axis=1
                )
            else:  # bewoodgrizz
                df['new_description'] = df.apply(
                    lambda row: clean_html(row['Shoper PL'], product_code=row['Seria']),
                    axis=1
                )

            if not safe_write_excel(df, output_files[vendor]):
                logger.error(f"Failed to write {vendor} data to Excel")

    except Exception as e:
        logger.error(f"Error in generate_clean_empty_descriptions: {str(e)}")

def generate_clean_descriptions(input_file: str, output_file: str):
    """Generate clean descriptions for all offers."""
    try:
        # Google Sheets with processed codes
        gsheets_url = 'https://docs.google.com/spreadsheets/d/1rz6QThoRfEreZWRczP0B8tuZoorVvSZlC7qWwryi-o0/export?format=csv&gid=0'
        
        logger.info('Reading Google Sheets data...')
        try:
            gsheets_data = pd.read_csv(gsheets_url)
        except Exception as e:
            logger.error(f"Error reading Google Sheets data: {str(e)}")
            return

        logger.info('Reading the input file...')
        df = safe_read_csv(input_file)
        if df is None:
            return

        # Data preprocessing
        df['description'] = df['description'].fillna('')
        gsheets_data['ean'] = gsheets_data['ean'].astype(str)
        df['product_code'] = df['product_code'].astype(str)

        # Filtering
        df = df[~df['title'].str.contains('|'.join(EXCLUDED_PRODUCTS), case=False, na=False)]
        mask = df['description'].str.contains('Bizon', case=False, na=False)
        products_to_change = df[mask].copy()

        logger.info('Creating copy with cleaned descriptions...')
        new_cols = products_to_change.apply(
            lambda row: clean_html(row['description'], product_code=row['product_code']),
            axis=1
        )
        products_to_change = pd.concat([products_to_change, new_cols], axis=1)

        logger.info(f'Saving {len(products_to_change)} to Excel...')
        if not safe_write_excel(products_to_change, output_file):
            logger.error("Failed to write data to Excel")
            return

        logger.info('Finished!')

    except Exception as e:
        logger.error(f"Error in generate_clean_descriptions: {str(e)}")

def generate_cleaned_descriptions_csv_to_xlsx():
    """Generate cleaned descriptions from CSV to XLSX."""
    try:
        input_file = FILE_PATHS['all_offers']
        output_file = FILE_PATHS['all_offers_cleaned']

        logger.info("Reading input CSV...")
        df = safe_read_csv(input_file)
        if df is None:
            return

        df['description'] = df['description'].fillna('')
        mask = df['description'].str.contains('-beta', case=False, na=False)
        products_to_change = df[mask].copy()

        logger.info('Creating copy with cleaned descriptions...')
        products_to_change['new_description'] = products_to_change['description'].apply(add_beta_classes)

        logger.info("Saving to Excel...")
        if not safe_write_excel(products_to_change, output_file):
            logger.error("Failed to write data to Excel")
            return

        logger.info(f"Done! Saved to {output_file}")

    except Exception as e:
        logger.error(f"Error in generate_cleaned_descriptions_csv_to_xlsx: {str(e)}")

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('end_data', exist_ok=True)
    
    # Run main processing
    # generate_cleaned_descriptions_csv_to_xlsx()
    
    generate_clean_descriptions(
        input_file=FILE_PATHS['all_offers'],
        output_file=FILE_PATHS['all_offers_ready']
    )

# extract_h3_from_descriptions(
#     input_file='data/all_offers.csv',
#     output_file='end_data/extracted_h3_values.xlsx'
# )
