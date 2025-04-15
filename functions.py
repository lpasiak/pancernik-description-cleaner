from bs4 import BeautifulSoup, NavigableString, Tag
import os

# Allowed tags and attributes
ALLOWED_TAGS = {'h2', 'h3', 'p', 'strong', 'em', 'img', 'hr', 'ul', 'li'}
ALLOWED_ATTRS = {
    'img': ['src', 'alt']
}

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
            p.unwrap()

def wrap_h3_content_in_em(soup):
    for h3 in soup.find_all('h3'):
        contents = h3.contents
        if len(contents) == 1 and isinstance(contents[0], Tag) and contents[0].name == 'em':
            continue
        text = h3.get_text(strip=True)
        h3.clear()
        em = soup.new_tag('em')
        em.string = text
        h3.append(em)

def add_beta_classes(soup):
    for tag_name in ALLOWED_TAGS:
        for tag in soup.find_all(tag_name):
            beta_class = f"{tag_name}-beta"
            existing_classes = tag.get("class", [])
            if beta_class not in existing_classes:
                tag['class'] = existing_classes + [beta_class]

def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")

    preserved_blocks = []

    # Preserve all .product-info blocks
    for i, div in enumerate(soup.find_all("div", class_="product-info")):
        placeholder = f"___PRODUCT_INFO_PLACEHOLDER_{i}___"
        preserved_blocks.append((placeholder, str(div)))
        div.replace_with(placeholder)

    # Preserve all .fx-iframeContainer blocks
    for i, div in enumerate(soup.find_all("div", class_="fx-iframeContainer")):
        placeholder = f"___IFRAME_CONTAINER_PLACEHOLDER_{i}___"
        preserved_blocks.append((placeholder, str(div)))
        div.replace_with(placeholder)

    for tag in soup.find_all():
        if tag.name == 'br':
            parent = tag.find_parent()
            if parent and parent.name in ['h2', 'h3']:
                continue  # keep <br> inside <h2> or <h3>
            tag.decompose()
            continue
        convert_span_to_p(tag)

    for tag in soup.find_all():
        if tag.name in ALLOWED_TAGS:
            allowed_attrs = ALLOWED_ATTRS.get(tag.name, [])
            allowed_attrs_lower = [a.lower() for a in allowed_attrs]
            for attr in list(tag.attrs):
                if attr.lower() not in allowed_attrs_lower:
                    del tag.attrs[attr]
        else:
            tag.unwrap()

    for tag in soup.find_all():
        if tag.name in ALLOWED_TAGS and is_empty_tag(tag):
            if tag.find('img'):
                continue
            tag.decompose()

    flatten_nested_tags(soup)
    unwrap_p_in_li(soup)
    unwrap_p_with_only_img(soup)
    wrap_h3_content_in_em(soup)
    add_beta_classes(soup)

    html = str(soup)
    lines = html.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    html_minified = '\n'.join(cleaned_lines)

    for placeholder, content in preserved_blocks:
        html_minified = html_minified.replace(placeholder, content)

    return html_minified
