import argparse
import json
import math
import os
import re
from pathlib import Path, PurePosixPath

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


JSON_FILEPATH = './data/books.json'
DOCROOT = './docs/'
IMAGE_DIR = './data/images/'
BOOK_DIR = './data/books/'
PAGE_DIR = './pages/'
BOOKS_ON_PAGE = 10


def get_txt_url(book_url, book_title):
    book_id = re.sub(r'[^\d*]', '', book_url)
    filename = re.sub(r'[^\w\d\. ]', '', f'{book_id}. {book_title}')
    filepath = PurePosixPath('..')/BOOK_DIR/f'{filename}.txt'
    return filepath


def load_books_from_json(filepath):
    with open(filepath, "r") as books_file:
        books_json = json.loads(books_file)
    books = [[PurePosixPath('..')/re.sub(r'^.*/', IMAGE_DIR, book['img_src']),
              book['title'],
              book['author'],
              get_txt_url(book['file_url'], book['title']),
              book['genres'],]
             for book in books_json]
    return books


def render_template(json_filepath):
    env = Environment(loader=FileSystemLoader('.'),
                      autoescape=select_autoescape(['html', 'xml']))
    template = env.get_template('template.html')

    all_books = load_books_from_json(json_filepath)
    for i, page_books in enumerate(list(chunked(all_books, BOOKS_ON_PAGE)), 1):
        rendered_page = template.render(
            books=list(chunked(page_books, 2)),
            pages_dir=PAGE_DIR,
            current=i,
            last=math.ceil(len(all_books)/BOOKS_ON_PAGE),
        )
        filepath = Path(os.getcwd())/DOCROOT/PAGE_DIR/f'index{i}.html'
        with open(filepath, 'w', encoding="utf8") as file:
            file.write(rendered_page)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Укажите имя JSON файла с данными'
    )
    parser.add_argument(
        'filepath', help="Путь и название файла",
        default=Path(DOCROOT)/JSON_FILEPATH, nargs='?',
    )
    args = parser.parse_args()
    books_filepath = args.filepath
    render_template(books_filepath)

    server = Server()
    server.watch('./template.html', lambda: render_template(books_filepath))
    server.serve(port=8000,
                 root=Path(DOCROOT),
                 default_filename='index.html',)
