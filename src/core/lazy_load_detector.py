"""Module for detecting and processing lazy-loaded content from Minecraft Wiki pages."""

from typing import List
from bs4 import BeautifulSoup


def find_lazy_load_pages(html_content: str) -> List[str]:
    """
    Find lazy-loaded subcategory pages from HTML content.

    Detects <div class="load-page"> elements with data-page attributes,
    extracts subcategory references, and constructs full URLs.
    Filters out "Changed" and "Removed" recipe sections.

    Args:
        html_content: HTML content from main wiki page

    Returns:
        List of full URLs to subcategory pages to download
    """
    soup = BeautifulSoup(html_content, "lxml")
    urls: List[str] = []

    # Find all lazy-load divs
    load_divs = soup.find_all("div", class_="load-page")

    for div in load_divs:
        # Extract data-page attribute
        page_ref = div.get("data-page", "")

        if not page_ref:
            continue

        # Filter out Changed and Removed recipe sections
        if "changed" in page_ref.lower() or "removed" in page_ref.lower():
            continue

        # Replace spaces with underscores for valid wiki URLs
        page_ref = page_ref.replace(" ", "_")

        # Construct full URL
        url = f"https://minecraft.wiki/w/{page_ref}"
        urls.append(url)

    return urls
