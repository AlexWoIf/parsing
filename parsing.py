import re
import os
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BOOK_DIR = 'books/'
IMAGE_DIR = 'images/'
SITE_URL = 'https://tululu.org/'
DOWNLOAD_URL = '/txt.php?id='
POST_URL = '/b'
TITLE_DELIMITER = ' \xa0 :: \xa0 '


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError


def parse_post_page(html):
    soup = BeautifulSoup(html, 'lxml')
    file_link = soup.find('a', string='скачать txt')
    if not file_link:
        return
    return {
        'file_url': file_link['href'],
        'title': file_link['title'][:-20],
        'img_src': soup.find('div', {'class': 'bookimage'})
                       .find('img').get('src'),
        'comments': [c.text for c in soup.select('div[class=texts] > span')],
        'genres': [a.text for a in soup.select('span.d_book > a')],
    }


def get_post_page(url):
    res = requests.get(url)
    res.raise_for_status()
    check_for_redirect(res)
    return res


def get_book_file(url):
    res = requests.get(url)
    res.raise_for_status()
    check_for_redirect(res)
    return res


def download_txt(url, filename, folder=BOOK_DIR):
    res = get_book_file(url)
    filename = re.sub(r'[^\w\d\. ]', '', filename) + '.txt'
    filepath = os.path.join(folder, filename)
    with open(filepath, 'wb') as file:
        file.write(res.content)
    return filepath


def download_image(url, filename, folder=BOOK_DIR):
    res = requests.get(url)
    res.raise_for_status()
    check_for_redirect(res)
    name = url.split('/')[-1]
    if filename:
        ext = (name+'.').split('.')[1]
        filename = ''.join(re.sub(r'[^\w\d\. ]', '', filename), '.', ext)
    else:
        filename = name
    filepath = os.path.join(folder, filename)
    with open(filepath, 'wb') as file:
        file.write(res.content)
    return filepath


if __name__ == "__main__":
    Path(BOOK_DIR).mkdir(parents=True, exist_ok=True)
    Path(IMAGE_DIR).mkdir(parents=True, exist_ok=True)
    for id in range(1, 11):
        try:
            res = get_post_page(urljoin(SITE_URL, f'{POST_URL}{id}/'))
            page_data = parse_post_page(res.text)
            if not page_data:
                print('not found')
                continue
            print(page_data)
            file_url, title, img_url, *_ = page_data.values()
            download_txt(urljoin(SITE_URL, file_url), f'{id}. {title}')
            download_image(urljoin(SITE_URL, img_url), '', IMAGE_DIR)
        except requests.exceptions.HTTPError:
            print('HTTP error')
            continue
