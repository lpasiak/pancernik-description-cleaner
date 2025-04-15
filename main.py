import os
from functions import clean_html
import pandas as pd

# File paths
input_file = 'data/all_offers.csv'
output_file = 'end_data/all_offers_ready.xlsx'

print('Reading the input file...')

df = pd.read_csv(input_file, delimiter=';')
mask = df['name'].str.contains('OUTLET: ', case=False)

print('Creating the copy with cleaned descriptions...')

all_outlets = df[mask].copy()
all_outlets['new_description'] = all_outlets['description'].apply(clean_html)

print(f'Saving {len(all_outlets)} to an excel file')

all_outlets.to_excel(output_file)

print('Finished!')
