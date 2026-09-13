import re
import unicodedata


def clean_text(raw_text: str) -> str:
    """
    Cleans raw extracted PDF text:
    - Strips page number artifacts and running headers/footers
    - Recombines hyphenated words broken across line breaks
    - Cleans non-printable control characters
    - Normalizes unicode whitespace and multiple newlines
    """
    if not raw_text:
        return ""

    # Normalize unicode (NFKC)
    text = unicodedata.normalize("NFKC", raw_text)

    # Remove null bytes and non-printable control characters (keep \n, \t, \r)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    # Remove common page number patterns
    # Examples: "Page 1 of 12", "Page 1 / 12", "- 1 -", "1 | Page"
    page_patterns = [
        r"(?i)\bpage\s+\d+\s*(?:of|/)\s*\d+\b",
        r"(?i)\bpage\s+\d+\b",
        r"(?m)^\s*[-—–]\s*\d+\s*[-—–]\s*$",
        r"(?m)^\s*\d+\s*\|\s*Page\s*$",
        r"(?m)^\s*\[\s*\d+\s*\]\s*$",
    ]
    for pattern in page_patterns:
        text = re.sub(pattern, "", text)

    # Remove common confidentiality / running headers & footers
    noise_patterns = [
        r"(?i)confidential\s*[-–]\s*for\s+internal\s+use\s+only",
        r"(?i)all\s+rights\s+reserved\.?",
        r"(?i)do\s+not\s+distribute\.?",
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, "", text)

    # Rejoin words hyphenated across line breaks: e.g. "con-\nnection" -> "connection"
    text = re.sub(r"(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)", r"\1\2", text)

    # Clean redundant whitespace on individual lines
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)

    # Collapse excessive consecutive line breaks (3 or more -> 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
