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
    parser = argparse.ArgumentParser(
        description='Парсер скачивает книги с сайта tululu.org '
                    'в указанном диапазоне id')
    parser.add_argument('--start_page', type=int,
                        help='Стартовая страница для парсинга', default=1, )
    parser.add_argument('--end_page', type=int,
                        help='Последняя страница для парсинга', default=701, )
    args = parser.parse_args()
    if args.start_page > args.end_page:
        parser.error('Стартовая страница не может быть больше начальной.')

    logging.basicConfig(level=logging.INFO)

    book_urls = []
    for page in range(args.start_page, args.end_page):
        url = urljoin(SCIFI_URL, str(page)+'/')
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        book_urls += [urljoin(url, tag_a.get('href'))
                      for tag_a in soup.select('div.bookimage > a')]

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
