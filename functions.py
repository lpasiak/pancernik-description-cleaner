from bs4 import BeautifulSoup, NavigableString, Tag
import os
import logging
from datetime import datetime

# Allowed tags and attributes
ALLOWED_TAGS = {'h2', 'h3', 'p', 'strong', 'em', 'img', 'hr', 'ul', 'li', 'br', 'a'}
ALLOWED_ATTRS = {
    'img': ['src', 'alt'],
    'a': ['href', 'target'],
    'p': ['class', 'id'],
    'h2': ['class', 'id']
}

def setup_logger():
    logs_dir = 'logs'
    os.makedirs(logs_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'clean_html_log-{timestamp}.txt'
    log_path = os.path.join(logs_dir, filename)

    logger = logging.getLogger('cleaner')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    return logger

logger = setup_logger()

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

    # If the tag has any non-whitespace NavigableString or any child Tag (like <br>), it's not empty
    for child in tag.children:
        if isinstance(child, Tag):
            return False  # it has nested tags (like <br>), keep it
        if isinstance(child, NavigableString) and child.strip():
            return False  # it has visible text
    return True

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

        inner_html = h3.decode_contents()  # ✅ preserves <br> and any nested tags
        h3.clear()

        em = soup.new_tag('em')
        em.append(BeautifulSoup(inner_html, 'html.parser'))  # ✅ parse back into Tag structure
        h3.append(em)

def add_beta_classes(soup):
    for tag_name in ALLOWED_TAGS:
        for tag in soup.find_all(tag_name):
            beta_class = f"{tag_name}-beta"
            existing_classes = tag.get("class", [])
            if beta_class not in existing_classes:
                tag['class'] = existing_classes + [beta_class]

def remove_empty_paragraphs(soup):
    for p in soup.find_all("p"):
        if not p.get_text(strip=True) and not p.find("img"):
            logger.info(f"Removing empty paragraph: {p}")
            p.decompose()

def unwrap_strong_inside_headings(soup):
    for tag in soup.find_all(['h2', 'h3']):
        for strong in tag.find_all('strong'):
            logger.info(f"Unwrapping <strong> inside <{tag.name}>: {strong}")
            strong.unwrap()

def clean_html(raw_html, product_code=None):
    logger.info(f"--- Cleaning started for product: {product_code} ---")

    raw_html = raw_html.replace('<br/>', '<br>').replace('<br />', '<br>')
    raw_html = raw_html.replace('<hr/>', '<hr>').replace('<hr />', '<hr>')
    soup = BeautifulSoup(raw_html, "html.parser")
    preserved_blocks = []

    def preserve_blocks(tag_class, label):
        for i, div in enumerate(soup.find_all("div", class_=tag_class)):
            placeholder = f"___{label.upper()}_PLACEHOLDER_{i}___"
            preserved_blocks.append((placeholder, str(div)))
            div.replace_with(placeholder)
            logger.info(f"Preserved <div class='{tag_class}'> as {placeholder}")

    preserve_blocks("product-info", "product_info")
    preserve_blocks("fx-iframeContainer", "iframe_container")

    for i, iframe in enumerate(soup.find_all("iframe")):
        placeholder = f"___IFRAME_TAG_PLACEHOLDER_{i}___"
        preserved_blocks.append((placeholder, str(iframe)))
        iframe.replace_with(placeholder)
        logger.info(f"Preserved <iframe> as {placeholder}")

    for tag in soup.find_all():
        convert_span_to_p(tag)

    for tag in soup.find_all():
        if tag.name in ALLOWED_TAGS:
            allowed_attrs = ALLOWED_ATTRS.get(tag.name, [])
            for attr in list(tag.attrs):
                if attr.lower() not in allowed_attrs:
                    del tag.attrs[attr]
                    logger.info(f"Removed disallowed attribute '{attr}' from <{tag.name}>")
        else:
            tag.unwrap()
            logger.info(f"Unwrapped disallowed tag <{tag.name}>")

    for tag in soup.find_all():
        if tag.name in ALLOWED_TAGS and is_empty_tag(tag):
            if tag.find('img'):
                continue
            tag.decompose()
            logger.info(f"Removed empty <{tag.name}> tag")

    def remove_consecutive_brs(soup):
        for tag in soup.find_all():
            prev = None
            for child in list(tag.children):
                if isinstance(child, Tag) and child.name == 'br':
                    if isinstance(prev, Tag) and prev.name == 'br':
                        logger.info(f"Removed consecutive <br> inside <{tag.name}>")
                        child.decompose()
                        continue
                prev = child

    flatten_nested_tags(soup)
    unwrap_p_in_li(soup)
    unwrap_strong_inside_headings(soup)
    wrap_h3_content_in_em(soup)
    add_beta_classes(soup)
    remove_consecutive_brs(soup)
    wrap_img_in_p(soup)
    remove_empty_paragraphs(soup)

    html = str(soup)
    lines = html.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    html_minified = '\n'.join(cleaned_lines)

    for placeholder, content in preserved_blocks:
        html_minified = html_minified.replace(placeholder, content)

    html_minified = html_minified.replace('<br/>', '<br>').replace('<br />', '<br>')
    logger.info(f"Finished cleaning product: {product_code}\n")
    return html_minified
