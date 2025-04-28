import pandas as pd
from functions import clean_html, remove_beta_classes
from compatibility import extract_h3_from_descriptions

def generate_clean_empty_descriptions():

    pancernik_input_file = 'data/pancernik_empty_offers.csv'
    bizon_input_file = 'data/bizon_empty_offers.csv'
    bewoodgrizz_input_file = 'data/bewoodgrizz_empty_offers.csv'

    pancernik_output_file = 'end_data/pancernik_empty_offers-result.xlsx'
    bizon_output_file = 'end_data/bizon_empty_offers-result.xlsx'
    bewoodgrizz_output_file = 'end_data/bewoodgrizz_empty_offers-result.xlsx'

    df_pancernik = pd.read_csv(pancernik_input_file, delimiter=';')
    df_bizon = pd.read_csv(bizon_input_file, delimiter=';')
    df_bewoodgrizz = pd.read_csv(bewoodgrizz_input_file, delimiter=';')

    df_pancernik['new_description'] = df_pancernik.apply(
        lambda row: clean_html(row['Opis PL'], product_code=row['Seria']),
        axis=1
    )

    df_bizon['new_description'] = df_bizon.apply(
        lambda row: clean_html(row['Opis Shoper'], product_code=row['Seria - Kolor']),
        axis=1
    )

    df_bewoodgrizz['new_description'] = df_bewoodgrizz.apply(
        lambda row: clean_html(row['Shoper PL'], product_code=row['Seria']),
        axis=1
    )

    df_pancernik.to_excel(pancernik_output_file, index=False)
    df_bizon.to_excel(bizon_output_file, index=False)
    df_bewoodgrizz.to_excel(bewoodgrizz_output_file, index=False)

def generate_clean_descriptions(input_file, output_file):

    # Google Sheets with processed codes
    gsheets_url = 'https://docs.google.com/spreadsheets/d/1rz6QThoRfEreZWRczP0B8tuZoorVvSZlC7qWwryi-o0/export?format=csv&gid=0'
    gsheets_data = pd.read_csv(gsheets_url)

    print('📥 Reading the input file...')
    df = pd.read_csv(input_file, delimiter=';')

    # Fill missing values
    df['producer'] = df['producer'].fillna('')
    df['description'] = df['description'].fillna('')

    gsheets_data['ean'] = gsheets_data['ean'].astype(str)
    df['product_code'] = df['product_code'].astype(str)

    # Exclude already processed product codes
    # df = df[~df['product_code'].isin(gsheets_data['ean'])]
    df = df[~df['product_code'].str.contains('szablon-aukcji', case=False, na=False)]
    df = df[~df['description'].str.contains('class="product-info"', case=False, na=False)]

    # Filter for specific producers
    mask = df['description'].str.contains('font-size', case=False, na=False)
    

    print('🛠️ Creating copy with cleaned descriptions...')
    products_to_change = df[mask].copy()

    # Apply clean_html with logging per product_code
    products_to_change['new_description'] = products_to_change.apply(
        lambda row: clean_html(row['description'], product_code=row['product_code']),
        axis=1
    )

    print(f'💾 Saving {len(products_to_change)} to Excel...')
    products_to_change.to_excel(output_file, index=False)
    print('✅ Finished!')

def generate_cleaned_descriptions_csv_to_xlsx():
    input_file = 'data/all_offers.csv'
    output_file = 'end_data/all_offers_cleaned.xlsx'

    print("📥 Reading input CSV...")
    df = pd.read_csv(input_file, delimiter=';')
    df['description'] = df['description'].fillna('')

    mask = df['description'].str.contains('-beta', case=False, na=False)

    print('🛠️ Creating copy with cleaned descriptions...')
    products_to_change = df[mask].copy()

    print("🧹 Cleaning HTML in 'description' column...")
    products_to_change['new_description'] = products_to_change.apply(
        lambda row: remove_beta_classes(row['description']),
        axis=1
    )

    print("💾 Saving to Excel...")
    products_to_change.to_excel(output_file, index=False)
    print(f"✅ Done! Saved to {output_file}")

generate_cleaned_descriptions_csv_to_xlsx()

generate_clean_descriptions(
    input_file='data/all_offers.csv',
    output_file = 'end_data/all_offers_ready.xlsx'
)

extract_h3_from_descriptions(
    input_file='data/all_offers.csv',
    output_file='end_data/extracted_h3_values.xlsx'
)
