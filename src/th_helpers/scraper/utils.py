# package imports
from bs4 import BeautifulSoup
from contextlib import closing
from requests import get


def get_html(url):
    """ scrapes a webpage and returns the beautified soup """
    with closing(get(url, stream=True)) as resp:
        return BeautifulSoup(resp.content, 'html.parser')


def extract_table_rows(html, class_name):
    """ extract the table from beautiful soup data given class name """
    table = html.find('table', {'class': class_name})
    rows = table.findAll('tr')
    del rows[0]
    return rows
