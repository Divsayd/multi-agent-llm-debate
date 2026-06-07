"""
read_website.py
Reads a business website URL, prints human-readable content,
and analyzes headlines for any keyword (default: Iran).

Dependencies: pip install requests beautifulsoup4 --user
Usage:
    python read_website.py https://news.ycombinator.com
    python read_website.py https://bbc.com/news Iran
    python read_website.py https://bbc.com/news Russia
"""

import re
import sys
import textwrap
import pdb; pdb.set_trace()

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing dependencies. Run: pip install requests beautifulsoup4 --user")
    sys.exit(1)

SKIP_TAGS = {"script", "style", "noscript", "header", "footer", "nav", "aside", "form", "meta", "head"}
CONTENT_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th", "blockquote", "figcaption", "label", "dt", "dd"}
HEADING_PREFIX = {"h1": "━━ ", "h2": "── ", "h3": "  • ", "h4": "    ◦ ", "h5": "      - ", "h6": "        · "}

HEADLINE_TAGS = {"h1", "h2", "h3", "h4", "a"}

WIDTH = 90


# ── Core fetch + parse ─────────────────────────────────────────────────────────

def fetch_soup(url: str) -> BeautifulSoup:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    headers = {"User-Agent": "Mozilla/5.0 (compatible; WebReader/1.0)"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def read_website(url: str, width: int = WIDTH) -> list[str]:
    """Return clean human-readable lines from a webpage."""
    soup = fetch_soup(url)
    for tag in soup(list(SKIP_TAGS)):
        tag.decompose()

    lines = []
    seen = set()

    for tag in soup.find_all(True):
        if tag.name not in CONTENT_TAGS:
            continue
        text = re.sub(r"\s+", " ", tag.get_text(separator=" ", strip=True)).strip()
        if not text or len(text) < 4:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)

        prefix = HEADING_PREFIX.get(tag.name, "")
        if tag.name in HEADING_PREFIX:
            if tag.name in ("h1", "h2"):
                lines.append("")
            wrapped = textwrap.wrap(text, width=width - len(prefix))
            lines.append(f"{prefix}{wrapped[0]}")
            for extra in wrapped[1:]:
                lines.append(" " * len(prefix) + extra)
        else:
            for w in textwrap.wrap(text, width=width - 2):
                lines.append("  " + w)

    return lines


# ── Headline extractor ─────────────────────────────────────────────────────────

def extract_headlines(url: str) -> list[str]:
    """Return deduplicated headlines (h1-h4, <a> links) from a page."""
    soup = fetch_soup(url)
    for tag in soup(list(SKIP_TAGS)):
        tag.decompose()

    seen = set()
    headlines = []
    for tag in soup.find_all(True):
        if tag.name not in HEADLINE_TAGS:
            continue
        text = re.sub(r"\s+", " ", tag.get_text(separator=" ", strip=True)).strip()
        if len(text) < 15 or len(text) > 300:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        headlines.append(text)

    return headlines[:80]


# ── Keyword analysis ───────────────────────────────────────────────────────────

def analyze_keyword(headlines: list[str], keyword: str) -> dict:
    """
    Scan headlines for keyword (case-insensitive).
    Returns a dict with matched lines, count, and a simple summary.
    """
    kw_lower = keyword.lower()
    matched = [h for h in headlines if kw_lower in h.lower()]

    if matched:
        summary = (
            f"Found {len(matched)} headline(s) mentioning '{keyword}' "
            f"out of {len(headlines)} total."
        )
    else:
        summary = f"No '{keyword}' news found across {len(headlines)} headlines."

    return {
        "keyword": keyword,
        "keyword_found": len(matched) > 0,
        "keyword_count": len(matched),
        "matched_headlines": matched,
        "total_scanned": len(headlines),
        "summary": summary,
    }


# ── Display helpers ────────────────────────────────────────────────────────────

def print_divider(char="=", label=""):
    if label:
        side = (WIDTH - len(label) - 2) // 2
        print(char * side + f" {label} " + char * side)
    else:
        print(char * WIDTH)


def display_website(url: str) -> None:
    """Fetch and print full readable content."""
    print_divider(label=f"Reading: {url}")
    lines = read_website(url)
    print("\n".join(lines))
    print_divider()
    print(f"  Total lines: {len(lines)}")
    print_divider()


def display_keyword_analysis(url: str, keyword: str) -> None:
    """Fetch headlines and report keyword matches."""
    print_divider(label=f"Keyword Analysis: '{keyword}'")
    print(f"  Source : {url}")
    print_divider("-")

    headlines = extract_headlines(url)
    result = analyze_keyword(headlines, keyword)

    print(f"  Headlines scanned : {result['total_scanned']}")
    print(f"  '{keyword}' mentions : {result['keyword_count']}")
    print_divider("-")

    if result["keyword_found"]:
        print(f"\n  ⚠  {keyword.upper()} NEWS DETECTED\n")
        for i, h in enumerate(result["matched_headlines"], 1):
            wrapped = textwrap.wrap(h, width=WIDTH - 6)
            print(f"  [{i}] {wrapped[0]}")
            for extra in wrapped[1:]:
                print(f"      {extra}")
        print()
    else:
        print(f"\n  ✓  NO {keyword.upper()} NEWS FOUND\n")

    print(f"  {result['summary']}")
    print_divider()


def display_full(url: str, keyword: str) -> None:
    """Print readable content AND keyword analysis."""
    display_website(url)
    print()
    display_keyword_analysis(url, keyword)