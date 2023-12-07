import logging
import argparse
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsing import (
    grab_book,
    BOOK_DIR,
    IMAGE_DIR)


SCIFI_URL = 'https://tululu.org/l55/'


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    book_urls = []
    for page in range(1, 5):
        url = urljoin(SCIFI_URL, str(page)+'/')
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        book_urls += [urljoin(url, tag_a['href'])
                      for tag_a in soup.select('div[class=bookimage] > a')]

    Path(BOOK_DIR).mkdir(parents=True, exist_ok=True)
    Path(IMAGE_DIR).mkdir(parents=True, exist_ok=True)
    books = []
    for book_url in book_urls:
        try:
            book = grab_book(book_url)
            books.append(book)
        except requests.exceptions.HTTPError as e:
            logging.warning(e)

    with open('books.json', 'w') as json_file:
        json.dump(books, json_file, ensure_ascii=False)
