# package imports
from bs4 import BeautifulSoup
from contextlib import closing
from requests import get


def get_html(url):
    """ scrapes a webpage and returns the beautified soup """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
    }
    with closing(get(url, headers=headers, stream=True, timeout=30)) as resp:
        resp.raise_for_status()
        return BeautifulSoup(resp.content, 'html.parser')


def extract_table_rows(html, class_name):
    """ extract the table from beautiful soup data given class name """
    table = html.find("table", {"class": class_name})
    if not table:
        return []  # or raise a custom exception
    rows = list(table.find_all("tr"))
    return rows[1:] if len(rows) > 1 else rows
