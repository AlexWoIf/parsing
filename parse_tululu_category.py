import logging
import argparse
import os
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsing import (grab_book, retry,
                     BOOK_DIR, IMAGE_DIR)


SCIFI_URL = 'https://tululu.org/l55/'
JSON_FILENAME = 'books.json'


@retry
def parse_category(page_url):
    response = requests.get(page_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    return [urljoin(page_url, tag_a.get('href'))
            for tag_a in soup.select('div.bookimage > a')]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Парсер скачивает книги с сайта tululu.org в указанном '
                    'диапазоне страниц из раздела научной фантастики '
                    'https://tululu.org/l55/')
    parser.add_argument('--start_page', type=int,
                        help='Стартовая страница для парсинга', default=1, )
    parser.add_argument('--end_page', type=int,
                        help='Страница до которой парсить', default=702, )
    parser.add_argument('--dest_folder', type=str,
                        help='Путь к каталогу с результатами парсинга: '
                        'картинкам, книгам, JSON', default='', )
    parser.add_argument('--skip_imgs',
                        help='Не скачивать картинки', action="store_true", )
    parser.add_argument('--skip_txt',
                        help='Не скачивать книги', action="store_true", )
    args = parser.parse_args()
    if args.start_page > args.end_page:
        parser.error('Стартовая страница не может быть больше начальной.')

    logging.basicConfig(level=logging.INFO)

    book_urls = []
    for page in range(args.start_page, args.end_page):
        page_url = urljoin(SCIFI_URL, str(page)+'/')
        try:
            book_urls += parse_category(page_url)
        except requests.exceptions.HTTPError as e:
            logging.warning(e)

    Path(args.dest_folder).mkdir(parents=True, exist_ok=True)
    book_dir = Path(args.dest_folder).joinpath(BOOK_DIR)
    if not args.skip_txt:
        book_dir.mkdir(parents=True, exist_ok=True)
    image_dir = Path(args.dest_folder).joinpath(IMAGE_DIR)
    if not args.skip_imgs:
        image_dir.mkdir(parents=True, exist_ok=True)
    books = []
    for book_url in book_urls:
        try:
            books.append(grab_book(book_url,
                                   skip_images=args.skip_imgs,
                                   skip_texts=args.skip_txt,
                                   image_dir=image_dir, book_dir=book_dir, ))
        except requests.exceptions.HTTPError as e:
            logging.warning(e)

    json_filepath = os.path.join(args.dest_folder, JSON_FILENAME)
    with open(json_filepath, 'w') as json_file:
        json.dump(books, json_file, ensure_ascii=False)
