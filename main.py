import os
import pandas as pd
from functions import clean_html

# File paths
input_file = 'data/all_offers.csv'
output_file = 'end_data/all_offers_ready.xlsx'

# Google Sheets with processed codes
gsheets_url = 'https://docs.google.com/spreadsheets/d/1rz6QThoRfEreZWRczP0B8tuZoorVvSZlC7qWwryi-o0/export?format=csv'
gsheets_data = pd.read_csv(gsheets_url)

print('📥 Reading the input file...')
df = pd.read_csv(input_file, delimiter=';')

# Fill missing values
df['producer'] = df['producer'].fillna('')
df['description'] = df['description'].fillna('')

# Exclude already processed product codes
df = df[~df['product_code'].isin(gsheets_data['ean'])]
df = df[~df['product_code'].str.contains('szablon-aukcji', case=False, na=False)]
# Filter for specific producers
mask = df['producer'].str.contains('Tactical', case=False, na=False)

print('🛠️ Creating copy with cleaned descriptions...')
all_outlets = df[mask].copy()

# Apply clean_html with logging per product_code
all_outlets['new_description'] = all_outlets.apply(
    lambda row: clean_html(row['description'], product_code=row['product_code']),
    axis=1
)

print(f'💾 Saving {len(all_outlets)} to Excel...')
all_outlets.to_excel(output_file, index=False)
print('✅ Finished!')
