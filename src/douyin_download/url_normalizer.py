import re

def extract_url_from_text(text: str) -> str | None:
    """Extract first URL from messy share text.

    Args:
        text: Raw text from clipboard

    Returns:
        Extracted URL or None if not found
    """
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    matches = re.findall(pattern, text)
    if not matches:
        return None
    url = matches[0]
    return url.rstrip('/')