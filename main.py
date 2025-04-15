import os
from functions import clean_html
import pandas as pd

# File paths
input_file = 'data/all_offers.csv'
output_file = 'end_data/all_offers_ready.csv'

final_html = clean_html(product_description)
