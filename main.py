from bs4 import BeautifulSoup, NavigableString, Tag
import os

# File paths
input_path = 'data/3666339149604.html'
output_path = 'end_data/3666339149604.html'

# Allowed tags and attributes
ALLOWED_TAGS = {'h2', 'h3', 'p', 'strong', 'em', 'img', 'hr', 'ul', 'li'}
ALLOWED_ATTRS = {
    'img': ['src', 'alt']
}

# CSS to prepend
STYLE_BLOCK = """
<style>
    body {
        font-family: 'Arial', sans-serif;
        width: 1180px;
        margin: 0 auto;
    }
    p {
        font-size: 12pt;
        color: #111;
    }
    h2:not(:first-of-type) {
        color: #be9c3f;
        margin-top: 40px;
    }
    h2 {
        text-align: center;
    }
    h3 {
        text-align: center;
    }
    img {
        display: block;
        max-width: 800px;
        height: auto;
        margin: 0 auto;
    }
</style>
"""

def convert_span_to_p(tag):
    if tag.name in ['span', 'div', 'font']:
        inline_tags = {'strong', 'em', 'a', 'img', 'hr'}
        if all(
            isinstance(child, NavigableString)
            or (isinstance(child, Tag) and child.name in inline_tags)
            for child in tag.contents
        ):
            tag.name = 'p'
        else:
            tag.unwrap()

def is_empty_tag(tag):
    if tag.name == 'img':
        return not tag.attrs.get('src')
    if tag.name == 'hr':
        return False
    text = tag.get_text().strip()
    return not text or text == '\xa0'

def flatten_nested_tags(soup):
    for outer_p in soup.find_all('p'):
        for inner_p in outer_p.find_all('p'):
            inner_p.unwrap()
    for heading in soup.find_all(['h2', 'h3']):
        for inner_p in heading.find_all('p'):
            inner_p.unwrap()

def unwrap_p_in_li(soup):
    for li in soup.find_all('li'):
        for p in li.find_all('p'):
            p.unwrap()

def unwrap_p_with_only_img(soup):
    for p in soup.find_all('p'):
        contents = [c for c in p.contents if not isinstance(c, NavigableString) or c.strip()]
        if len(contents) == 1 and isinstance(contents[0], Tag) and contents[0].name == 'img':
            print(f"🪄 Unwrapping <p> around <img>: {p}")
            p.unwrap()

def wrap_h3_content_in_em(soup):
    for h3 in soup.find_all('h3'):
        contents = h3.contents
        if len(contents) == 1 and isinstance(contents[0], Tag) and contents[0].name == 'em':
            continue  # already wrapped
        text = h3.get_text(strip=True)
        h3.clear()
        em = soup.new_tag('em')
        em.string = text
        h3.append(em)
        print(f"✨ Wrapped <h3> content in <em>: {h3}")

def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")

    print(f"📊 After parsing: {len(soup.find_all('img'))} <img> tags found")
    for i, tag in enumerate(soup.find_all('img'), 1):
        print(f"  {i}. Parsed <img>: {tag}")

    for tag in soup.find_all():
        if tag.name == 'br':
            tag.decompose()
            continue
        convert_span_to_p(tag)
        if tag.name == 'img':
            print(f"📦 After convert_span_to_p: {tag}")

    for tag in soup.find_all():
        if tag.name in ALLOWED_TAGS:
            allowed_attrs = ALLOWED_ATTRS.get(tag.name, [])
            allowed_attrs_lower = [a.lower() for a in allowed_attrs]
            for attr in list(tag.attrs):
                if attr.lower() not in allowed_attrs_lower:
                    print(f"🧹 Removing attr '{attr}' from <{tag.name}>")
                    del tag.attrs[attr]
            if tag.name == 'img':
                print(f"✂️ After attr cleanup: {tag}")
        else:
            tag.unwrap()

    for tag in soup.find_all():
        if tag.name in ALLOWED_TAGS and is_empty_tag(tag):
            if tag.find('img'):
                print(f"🚫 Skipping tag because it contains <img>: {tag}")
                continue
            print(f"🗑️ Removing empty tag: {tag}")
            tag.decompose()

    flatten_nested_tags(soup)
    unwrap_p_in_li(soup)
    unwrap_p_with_only_img(soup)
    wrap_h3_content_in_em(soup)  # ✅ NEW function call here

    print(f"🖼️ Final <img> count: {len(soup.find_all('img'))}")
    for i, tag in enumerate(soup.find_all('img'), 1):
        print(f"  {i}. Final <img>: {tag}")

    # Save intermediate debug HTML
    with open("debug_output.html", "w", encoding="utf-8") as debug_file:
        debug_file.write(str(soup))

    # Minify whitespace
    html = str(soup)
    lines = html.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    html_minified = '\n'.join(cleaned_lines)

    return html_minified

# Read raw HTML
with open(input_path, 'r', encoding='utf-8') as f:
    raw_html = f.read()

print("📥 Raw HTML contains <img>:", '<img' in raw_html.lower())

# Clean HTML
cleaned_body = clean_html(raw_html)

# Combine CSS + cleaned HTML
final_html = STYLE_BLOCK + '\n' + cleaned_body

# Ensure output directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Write final file
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(final_html)

print(f"✅ Cleaned HTML with CSS saved to: {output_path}")
