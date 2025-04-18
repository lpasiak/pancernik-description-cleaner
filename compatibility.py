from bs4 import BeautifulSoup, NavigableString, Tag
import pandas as pd

def extract_h3_from_descriptions(input_file, output_file):
    print("📥 Reading input file...")
    df = pd.read_csv(input_file, delimiter=';')
    df['description'] = df['description'].fillna('')

    def extract_h3_data(html):
        soup = BeautifulSoup(html, "html.parser")

        # All <h3>
        h3_tags = soup.find_all('h3')
        h3_texts = [tag.decode_contents() for tag in h3_tags]

        # Only <h3 class="h3-beta">
        h3_beta_tags = soup.find_all('h3', class_='h3-beta')
        h3_beta_texts = [tag.decode_contents() for tag in h3_beta_tags]

        return pd.Series({
            'extracted_h3': ' | '.join(h3_texts),
            'h3_count': len(h3_tags)
        })

    def prettify_html(html):
        soup = BeautifulSoup(html, "html.parser")
        return soup.prettify()

    print("🔍 Extracting <h3> tags and filtering class='h3-beta'...")
    h3_data = df['description'].apply(extract_h3_data)
    df['pretty_description'] = df['description'].apply(prettify_html)
    df = pd.concat([df, h3_data], axis=1)

    print(f"💾 Saving to: {output_file}")
    df.to_excel(output_file, index=False)
    print("✅ Done!")
