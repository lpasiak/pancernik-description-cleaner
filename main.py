import os
from functions import clean_html

# File paths
input_path = 'data/8809971229227.html'
output_path = 'end_data/8809971229227.html'



with open(input_path, 'r', encoding='utf-8') as f:
    raw_html = f.read()

cleaned_body = clean_html(raw_html)
final_html = cleaned_body

os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(final_html)
