from bs4 import BeautifulSoup, NavigableString, Tag
import pandas as pd
import re

def extract_h3_from_descriptions(input_file, output_file):
    print("📥 Reading input file...")
    df = pd.read_csv(input_file, delimiter=';')
    df['description'] = df['description'].fillna('')

    def extract_h3_data(html):
        soup = BeautifulSoup(html, "html.parser")

        # All <h3> and <h2>
        h3_tags = soup.find_all('h3')
        h2_tags = soup.find_all('h2')

        h3_inner = [tag.decode_contents() for tag in h3_tags]
        h3_full_html = [str(tag) for tag in h3_tags]

        # Create a unified block from all <h3> content
        merged_items = []

        for tag in h3_tags:
            em = tag.find('em')
            contents = em.contents if em else tag.contents

            for frag in contents:
                if isinstance(frag, Tag) and frag.name == 'br':
                    merged_items.append(str(frag))
                elif isinstance(frag, NavigableString) and frag.strip():
                    merged_items.append(str(frag))
                elif isinstance(frag, Tag):
                    merged_items.append(frag.decode())

        # Remove trailing <br> if exists
        while merged_items and merged_items[-1].strip() == '<br>':
            merged_items.pop()

        # Combine into <h3><em>…</em></h3> format
        if merged_items:
            combined = ''.join(
                frag if 'br' in frag else f"{frag}<br>"
                for frag in merged_items
            )

            # 🧼 Remove consecutive <br> or <br/> or <br /> — keep only one
            combined = re.sub(r'(<br\s*/?>\s*){2,}', '<br>', combined).rstrip('<br>')

            unified_h3 = f'<h3><em>{combined}</em></h3>'
        else:
            unified_h3 = ''


    # def prettify_html(html):
    #     soup = BeautifulSoup(html, "html.parser")
    #     return soup.prettify()

    print("🔍 Extracting <h3> and <h2> tags, and normalizing <h3>...")
    h3_data = df['description'].apply(extract_h3_data)

    # df['pretty_description'] = df['description'].apply(prettify_html)

    df = pd.concat([df, h3_data], axis=1)

    print(f"💾 Saving to: {output_file}")
    df.to_excel(output_file, index=False)
    print("✅ Done!")
