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


def check_for_redirect(response):
    if response.history:
        logging.warning(
                f'{response.history[0].url} не существует. '
                f'Перенаправлены на {response.url}')
        raise requests.exceptions.HTTPError


def parse_book_page(html):
    soup = BeautifulSoup(html, 'lxml')
    file_link = soup.find('a', string='скачать txt')
    if not file_link:
        logging.warning(
                f'На странице книги {response.request.url} '
                f'нет ссылки на скачивание файла.')
        raise requests.exceptions.HTTPError
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
        parser.error('Стартовый id не может быть меньше конечного.')

    logging.basicConfig(level=logging.INFO)

    Path(BOOK_DIR).mkdir(parents=True, exist_ok=True)
    Path(IMAGE_DIR).mkdir(parents=True, exist_ok=True)
    for book_id in range(args.start_id, args.end_id+1):
        delay = 0
        while True:
            try:
                book_url = urljoin(SITE_URL, f'/b{book_id}/')
                response = requests.get(book_url)
                response.raise_for_status()
                check_for_redirect(response)

                page_data = parse_book_page(response.text)
                file_url, img_url, title, *_ = page_data.values()
                download_txt(
                    urljoin(book_url, file_url), f'{book_id}. {title}'
                )
                download_image(urljoin(book_url, img_url), '', IMAGE_DIR)

                delay = 0
                break
            except requests.exceptions.HTTPError:
                delay = 0
                break
            except requests.exceptions.ConnectionError:
                logging.warning('Сеть недоступна, пробуем еще раз. '
                                f'Задержка перед попыткой {delay}секунд.')
                sleep(delay)
                delay += 5
