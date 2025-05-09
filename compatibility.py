from bs4 import BeautifulSoup, NavigableString, Tag
import pandas as pd
import re

def extract_h3_from_descriptions(input_file, output_file):
    print("📥 Reading input file...")
    df = pd.read_csv(input_file, delimiter=';')
    df['description'] = df['description'].fillna('')

    def extract_h3_data_and_replace(html):
        soup = BeautifulSoup(html, "html.parser")

        h3_tags = soup.find_all('h3')
        h2_tags = soup.find_all('h2')

        h3_inner = [tag.decode_contents() for tag in h3_tags]
        h3_full_html = [str(tag) for tag in h3_tags]

        # Build unified <h3><em>...</em></h3>
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

        while merged_items and merged_items[-1].strip() == '<br>':
            merged_items.pop()

        if merged_items:
            combined = ''.join(
                frag if 'br' in frag else f"{frag}<br>"
                for frag in merged_items
            )
            combined = re.sub(r'(<br\s*/?>\s*){2,}', '<br>', combined).rstrip('<br>')
            unified_h3_html = f'<h3><em>{combined}</em></h3>'
        else:
            unified_h3_html = ''

        if h3_tags and unified_h3_html:
            first_h3 = h3_tags[0]
            unified_h3_tag = BeautifulSoup(unified_h3_html, 'html.parser').h3
            first_h3.replace_with(unified_h3_tag)
            for h3 in h3_tags[1:]:
                h3.decompose()

        # ✅ Add opening and closing tags in order
        tag_sequence = []

        def walk(tag):
            if not isinstance(tag, Tag):
                return
            tag_sequence.append(f"<{tag.name}>")
            for child in tag.children:
                if isinstance(child, Tag):
                    walk(child)
            tag_sequence.append(f"</{tag.name}>")

        walk(soup)

        return pd.Series({
            'extracted_h3': ' | '.join(h3_inner),
            'raw_h3_tags': ' | '.join(h3_full_html),
            'h3_count': len(h3_tags),
            'h2_count': len(h2_tags),
            'unified_h3': unified_h3_html,
            'new_description_with_unified_h3': str(soup),
            'HTML Tags': ' | '.join(tag_sequence)
        })

    print("🔍 Extracting and normalizing <h3> content...")
    h3_data = df['description'].apply(extract_h3_data_and_replace)
    df = pd.concat([df, h3_data], axis=1)

    print(f"💾 Saving to: {output_file}")
    df.to_excel(output_file, index=False)
    print("✅ Done!")
