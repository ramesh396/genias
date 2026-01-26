import re
import html

def clean_html(text):
    if not text:
        return ""

    text = re.sub(r'<[^>]+>', '', text)   # remove html tags
    text = html.unescape(text)            # convert all HTML entities

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n'.join(lines)
