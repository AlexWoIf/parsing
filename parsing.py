import re
import os
from time import sleep
import logging
import argparse
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BOOK_DIR = 'books/'
IMAGE_DIR = 'images/'
SITE_URL = 'https://tululu.org/'


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
    file_link = soup.find('a', string='скачать txt')
    if not file_link:
        raise requests.exceptions.HTTPError(
                f'На странице книги {response.request.url} '
                f'нет ссылки на скачивание файла.'
        )
    return {
        'file_url': file_link['href'],
        'img_src': soup.find('div', {'class': 'bookimage'})
                       .find('img').get('src'),
        'title': file_link['title'][:-20],
        'author': soup.find('h1').find('a').text,
        'comments': [c.text for c in soup.select('div[class=texts] > span')],
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
def grab_book(book_url):
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
    download_txt(
        urljoin(book_url, file_url), f'{book_id}. {title}'
    )
    download_image(urljoin(book_url, img_url), '', IMAGE_DIR)

    return book


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Парсер скачивает книги с сайта tululu.org '
                    'в указанном диапазоне id')
    parser.add_argument('--start_id', type=int,
                        help='Стартовый id для парсинга', default=1, )
    parser.add_argument('--end_id', type=int,
                        help='Последний id для парсинга', default=10, )
    args = parser.parse_args()
    if args.start_id > args.end_id:
        parser.error('Стартовый id не может быть больше конечного.')

    logging.basicConfig(level=logging.INFO)

    Path(BOOK_DIR).mkdir(parents=True, exist_ok=True)
    Path(IMAGE_DIR).mkdir(parents=True, exist_ok=True)
    for book_id in range(args.start_id, args.end_id+1):
        book_url = urljoin(SITE_URL, f'/b{book_id}/')
        try:
            grab_book(book_url)
        except requests.exceptions.HTTPError as e:
            logging.warning(e)
