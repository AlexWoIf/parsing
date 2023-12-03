import re
import os
from pathlib import Path
import requests
from bs4 import BeautifulSoup


BOOK_DIR = 'books/'
DOWNLOAD_URL = 'https://tululu.org/txt.php?id='
POST_URL = 'https://tululu.org/b'
TITLE_DELIMITER = ' \xa0 :: \xa0 '


def check_for_redirect(response):
    print(response.history)
    if response.history:
        raise requests.exceptions.HTTPError


def parse_page_by_id(id):
    res = requests.get(url=f'{POST_URL}{id}/')
    print(f'{POST_URL}{id}', res)
    res.raise_for_status()
    check_for_redirect(res)
    soup = BeautifulSoup(res.text, 'lxml')
    return soup.find('h1').text.split(TITLE_DELIMITER)


def get_book_by_url(url):
    res = requests.get(url)
    res.raise_for_status()
    check_for_redirect(res)
    return res


def download_txt(url, filename, folder=BOOK_DIR):
    res = get_book_by_url(url)
    filename = re.sub(r'[^\w ]', '', filename)+'.txt'
    filepath = os.path.join(folder, filename)
    with open(filepath, 'wb') as file:
        file.write(res.content)
    return filepath


if __name__ == "__main__":
    Path(BOOK_DIR).mkdir(parents=True, exist_ok=True)
    for id in range(1, 11):
        print(id)
        try:
            title, _ = parse_page_by_id(id)
            print(title)
            download_txt(f'{DOWNLOAD_URL}{id}', title)
            print(parse_page_by_id(id))
        except requests.exceptions.HTTPError:
            print('error')
            continue
