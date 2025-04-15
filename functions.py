from bs4 import BeautifulSoup, NavigableString, Tag
import os

# Allowed tags and attributes
ALLOWED_TAGS = {'h2', 'h3', 'p', 'strong', 'em', 'img', 'hr', 'ul', 'li', 'br'}
ALLOWED_ATTRS = {
    'img': ['src', 'alt']
}

def convert_span_to_p(tag):
    if tag.name in ['span', 'div', 'font']:
        inline_tags = {'strong', 'em', 'a', 'img', 'hr', 'br'}
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
    if tag.name in ['hr', 'br']:
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

def wrap_img_in_p(soup):
    for img in soup.find_all('img'):
        parent = img.parent
        if parent.name != 'p' or len(parent.contents) > 1:
            new_p = soup.new_tag("p")
            img.insert_before(new_p)
            new_p.append(img.extract())

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
    # Normalize self-closing <br/> and <hr/> to standard <br> and <hr>
    raw_html = raw_html.replace('<br/>', '<br>').replace('<br />', '<br>')
    raw_html = raw_html.replace('<hr/>', '<hr>').replace('<hr />', '<hr>')

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

    # Preserve all standalone <iframe> tags
    for i, iframe in enumerate(soup.find_all("iframe")):
        placeholder = f"___IFRAME_TAG_PLACEHOLDER_{i}___"
        preserved_blocks.append((placeholder, str(iframe)))
        iframe.replace_with(placeholder)

    # Convert span/font/div to <p> where appropriate
    for tag in soup.find_all():
        convert_span_to_p(tag)

    # Remove unwanted attributes from allowed tags, unwrap disallowed tags
    for tag in soup.find_all():
        if tag.name in ALLOWED_TAGS:
            allowed_attrs = ALLOWED_ATTRS.get(tag.name, [])
            allowed_attrs_lower = [a.lower() for a in allowed_attrs]
            for attr in list(tag.attrs):
                if attr.lower() not in allowed_attrs_lower:
                    del tag.attrs[attr]
        else:
            tag.unwrap()

    # Remove empty allowed tags (but preserve <img> inside them)
    for tag in soup.find_all():
        if tag.name in ALLOWED_TAGS and is_empty_tag(tag):
            if tag.find('img'):
                continue
            tag.decompose()

    flatten_nested_tags(soup)
    unwrap_p_in_li(soup)
    wrap_h3_content_in_em(soup)
    add_beta_classes(soup)
    wrap_img_in_p(soup)  # ✅ NEW unified image wrapper

    html = str(soup)
    lines = html.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    html_minified = '\n'.join(cleaned_lines)

    # Restore preserved HTML blocks
    for placeholder, content in preserved_blocks:
        html_minified = html_minified.replace(placeholder, content)

    # Normalize <br/> back to <br> just before output
    html_minified = html_minified.replace('<br/>', '<br>').replace('<br />', '<br>')

    return html_minified
