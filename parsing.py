import re
import os
from time import sleep
import logging
import argparse
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BOOK_DIR = 'books/'
IMAGE_DIR = 'images/'
SITE_URL = 'https://tululu.org/'
JSON_FILENAME = 'books.json'


def retry(func):
    def _wrapper(*args, **kwargs):
        delay = 0
        while True:
            try:
                return_value = func(*args, **kwargs)
                return return_value
            except requests.exceptions.ConnectionError:
                logging.warning('Сеть недоступна, пробуем еще раз. '
                                f'Задержка перед попыткой {delay} секунд.')
                sleep(delay)
                delay += 5
    return _wrapper


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError(
                f'{response.history[0].url} не существует. '
                f'Перенаправлены на {response.url}'
        )


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    file_link = soup.select_one('a[title$="скачать книгу txt"]')
    if not file_link:
        raise requests.exceptions.HTTPError(
                f'На странице книги {response.request.url} '
                f'нет ссылки на скачивание файла.'
        )
    return {
        'file_url': file_link['href'],
        'img_src': soup.select_one('div.bookimage  img').get('src'),
        'title': file_link['title'][:-20],
        'author': soup.select_one('h1 a').text,
        'comments': [c.text for c in soup.select('div.texts > span')],
        'genres': [a.text for a in soup.select('span.d_book > a')],
    }


def download_txt(url, filename, folder=BOOK_DIR):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    filename = re.sub(r'[^\w\d\. ]', '', filename) + '.txt'
    filepath = os.path.join(folder, filename)
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def download_image(url, filename, folder=BOOK_DIR):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    name = url.split('/')[-1]
    if filename:
        ext = (name+'.').split('.')[1]
        filename = ''.join(re.sub(r'[^\w\d\. ]', '', filename), '.', ext)
    else:
        filename = name
    filepath = os.path.join(folder, filename)
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


@retry
def grab_book(book_url, skip_images=False, skip_texts=False,
              book_dir=BOOK_DIR, image_dir=IMAGE_DIR):
    match = re.search(r'b(\d+)/$', book_url)
    if not match:
        raise requests.exceptions.HTTPError(
            f'В ссылке отсутствует ID книги: {book_url}'
        )
    book_id = match[1]

    response = requests.get(book_url)
    response.raise_for_status()
    check_for_redirect(response)

    book = parse_book_page(response)
    file_url, img_url, title, *_ = book.values()
    if not skip_texts:
        download_txt(
            urljoin(book_url, file_url), f'{book_id}. {title}', book_dir,
        )
    if not skip_images:
        download_image(urljoin(book_url, img_url), '', image_dir)

    return book


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Парсер скачивает книги с сайта tululu.org '
                    'в указанном диапазоне id')
    parser.add_argument('--start_id', type=int,
                        help='Стартовый id для парсинга', default=1, )
    parser.add_argument('--end_id', type=int,
                        help='Последний id для парсинга', default=10, )
    parser.add_argument('--dest_folder', type=str,
                        help='Путь к каталогу с результатами парсинга: '
                        'картинкам, книгам, JSON', default='', )
    parser.add_argument('--skip_imgs',
                        help='Не скачивать картинки', action="store_true", )
    parser.add_argument('--skip_txt',
                        help='Не скачивать книги', action="store_true", )
    args = parser.parse_args()
    if args.start_id > args.end_id:
        parser.error('Стартовый id не может быть больше конечного.')

    logging.basicConfig(level=logging.INFO)

    Path(args.dest_folder).mkdir(parents=True, exist_ok=True)
    book_dir = Path(args.dest_folder).joinpath(BOOK_DIR)
    if not args.skip_txt:
        book_dir.mkdir(parents=True, exist_ok=True)
    image_dir = Path(args.dest_folder).joinpath(IMAGE_DIR)
    if not args.skip_imgs:
        image_dir.mkdir(parents=True, exist_ok=True)

    books = []
    for book_id in range(args.start_id, args.end_id+1):
        book_url = urljoin(SITE_URL, f'/b{book_id}/')
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
