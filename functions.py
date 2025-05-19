from bs4 import BeautifulSoup, NavigableString, Tag
import os
from datetime import datetime
import pandas as pd
from typing import Optional, Dict, List, Union
import re
from pathlib import Path
from config import ALLOWED_TAGS, ALLOWED_ATTRS, BETA_CLASS_SUFFIX

class HTMLValidationError(Exception):
    """Custom exception for HTML validation errors."""
    pass

def validate_html(html: str) -> bool:
    """Validate if the input is valid HTML."""
    try:
        if not html or not isinstance(html, str):
            print(f"Invalid input type: {type(html)}")
            return False
            
        # Check for basic HTML structure
        if not ('<' in html and '>' in html):
            print("Input does not contain HTML tags")
            return False
            
        BeautifulSoup(html, "html.parser")
        return True
    except Exception as e:
        print(f"HTML validation error: {str(e)}")
        return False

def convert_span_to_p(tag: Tag) -> None:
    """Convert span tags to paragraph tags when appropriate."""
    try:
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
    except Exception:
        pass

def add_beta_classes(html: str) -> str:
    """Add beta classes to HTML tags."""
    try:
        if not html or not isinstance(html, str):
            print(f"Invalid input type for beta classes: {type(html)}")
            return html
            
        if not validate_html(html):
            print(f"Invalid HTML input for beta class addition. First 100 chars: {html[:100]}")
            return html

        soup = BeautifulSoup(html, "html.parser")
        modified_tags = 0
        
        for tag in soup.find_all(True):
            class_name = f"{tag.name}{BETA_CLASS_SUFFIX}"
            existing_classes = tag.get("class", [])
            if class_name not in existing_classes:
                tag['class'] = existing_classes + [class_name]
                modified_tags += 1
                
        if modified_tags > 0:
            print(f"Added beta classes to {modified_tags} tags")
            
        return str(soup)
    except Exception as e:
        print(f"Error adding beta classes: {str(e)}")
        return html

def is_empty_tag(tag: Tag) -> bool:
    """Check if a tag is empty."""
    try:
        if tag.name == 'img':
            return not tag.attrs.get('src')
        if tag.name in ['hr', 'br']:
            return False

        for child in tag.children:
            if isinstance(child, Tag):
                return False
            if isinstance(child, NavigableString) and child.strip():
                return False
        return True
    except Exception:
        return False

def flatten_nested_tags(soup: BeautifulSoup) -> None:
    """Flatten nested tags in the HTML."""
    try:
        for outer_p in soup.find_all('p'):
            for inner_p in outer_p.find_all('p'):
                inner_p.unwrap()
        for heading in soup.find_all(['h2', 'h3']):
            for inner_p in heading.find_all('p'):
                inner_p.unwrap()
    except Exception:
        pass

def unwrap_p_in_li(soup: BeautifulSoup) -> None:
    """Unwrap paragraph tags inside list items."""
    try:
        for li in soup.find_all('li'):
            for p in li.find_all('p'):
                p.unwrap()
    except Exception:
        pass

def wrap_img_in_p(soup: BeautifulSoup) -> None:
    """Wrap image tags in paragraph tags."""
    try:
        for img in soup.find_all('img'):
            parent = img.parent
            if parent.name != 'p' or len(parent.contents) > 1:
                new_p = soup.new_tag("p")
                img.insert_before(new_p)
                new_p.append(img.extract())
    except Exception:
        pass

def wrap_h3_content_in_em(soup: BeautifulSoup) -> None:
    """Wrap h3 content in emphasis tags."""
    try:
        for h3 in soup.find_all('h3'):
            contents = h3.contents
            if len(contents) == 1 and isinstance(contents[0], Tag) and contents[0].name == 'em':
                continue

            inner_html = h3.decode_contents()
            h3.clear()

            em = soup.new_tag('em')
            em.append(BeautifulSoup(inner_html, 'html.parser'))
            h3.append(em)
    except Exception:
        pass

def remove_empty_paragraphs(soup: BeautifulSoup) -> None:
    """Remove empty paragraph tags."""
    try:
        for p in soup.find_all("p"):
            if not p.get_text(strip=True) and not p.find("img"):
                p.decompose()
    except Exception:
        pass

def unwrap_strong_inside_headings(soup: BeautifulSoup) -> None:
    """Unwrap strong tags inside headings."""
    try:
        for tag in soup.find_all(['h2', 'h3']):
            for strong in tag.find_all('strong'):
                strong.unwrap()
    except Exception:
        pass

def clean_html(raw_html: str, product_code: Optional[str] = None) -> pd.Series:
    """Clean and sanitize HTML content."""
    try:
        if not raw_html or not isinstance(raw_html, str):
            print(f"Invalid input type for product {product_code}: {type(raw_html)}")
            return pd.Series({'new_description': raw_html})
            
        if not validate_html(raw_html):
            print(f"Invalid HTML for product code: {product_code}. First 100 chars: {raw_html[:100]}")
            return pd.Series({'new_description': raw_html})

        # Normalize line endings and self-closing tags
        raw_html = raw_html.replace('<br/>', '<br>').replace('<br />', '<br>')
        raw_html = raw_html.replace('<hr/>', '<hr>').replace('<hr />', '<hr>')
        
        soup = BeautifulSoup(raw_html, "html.parser")
        preserved_blocks = []

        def preserve_blocks(tag_class: str, label: str) -> None:
            """Preserve specific blocks of HTML."""
            try:
                for i, div in enumerate(soup.find_all("div", class_=tag_class)):
                    placeholder = f"___{label.upper()}_PLACEHOLDER_{i}___"
                    preserved_blocks.append((placeholder, str(div)))
                    div.replace_with(placeholder)
            except Exception:
                pass

        # Preserve important blocks
        preserve_blocks("product-info", "product_info")
        preserve_blocks("fx-iframeContainer", "iframe_container")

        # Preserve iframes
        for i, iframe in enumerate(soup.find_all("iframe")):
            placeholder = f"___IFRAME_TAG_PLACEHOLDER_{i}___"
            preserved_blocks.append((placeholder, str(iframe)))
            iframe.replace_with(placeholder)

        # Process tags
        for tag in soup.find_all():
            convert_span_to_p(tag)

        # Clean attributes
        for tag in soup.find_all():
            if tag.name in ALLOWED_TAGS:
                allowed_attrs = ALLOWED_ATTRS.get(tag.name, [])
                for attr in list(tag.attrs):
                    if attr.lower() not in allowed_attrs:
                        del tag.attrs[attr]
            else:
                tag.unwrap()

        # Remove empty tags
        for tag in soup.find_all():
            if tag.name in ALLOWED_TAGS and is_empty_tag(tag):
                if tag.find('img'):
                    continue
                tag.decompose()

        def remove_consecutive_brs(soup: BeautifulSoup) -> None:
            """Remove consecutive break tags."""
            try:
                for tag in soup.find_all():
                    prev = None
                    for child in list(tag.children):
                        if isinstance(child, Tag) and child.name == 'br':
                            if isinstance(prev, Tag) and prev.name == 'br':
                                child.decompose()
                                continue
                        prev = child
            except Exception:
                pass

        # Apply all cleaning functions
        flatten_nested_tags(soup)
        unwrap_p_in_li(soup)
        unwrap_strong_inside_headings(soup)
        wrap_h3_content_in_em(soup)
        remove_consecutive_brs(soup)
        wrap_img_in_p(soup)
        remove_empty_paragraphs(soup)

        # Finalize HTML
        html = str(soup)
        lines = html.splitlines()
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        html_minified = '\n'.join(cleaned_lines)

        # Restore preserved blocks
        for placeholder, content in preserved_blocks:
            html_minified = html_minified.replace(placeholder, content)

        html_minified = html_minified.replace('<br/>', '<br>').replace('<br />', '<br>')
        
        return pd.Series({
            'new_description': html_minified
        })

    except Exception as e:
        print(f"Error cleaning HTML for product code {product_code}: {str(e)}")
        return pd.Series({
            'new_description': raw_html  # Return original HTML on error
        })

# def remove_beta_classes(html: str) -> str:
#     soup = BeautifulSoup(html, "html.parser")

#     for tag in soup.find_all(True):  # True = all tags
#         classes = tag.get("class", [])
#         filtered_classes = [cls for cls in classes if not cls.endswith("-beta")]
#         if classes != filtered_classes:
#             tag['class'] = filtered_classes
#             if not tag['class']:
#                 del tag['class']  # remove empty class attribute

#     return str(soup)