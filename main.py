import os
from functions import clean_html
import pandas as pd

# File paths
input_file = 'data/all_offers.csv'
output_file = 'end_data/all_offers_ready.csv'

df = pd.read_csv(input_file, delimiter=';')
mask = df['name'].str.contains('OUTLET: ', case=False)

all_outlets = df[mask].copy()
all_outlets['new_description'] = all_outlets['description'].apply(clean_html)

all_outlets.to_csv(output_file, sep=';')
