from jinja2 import Environment, FileSystemLoader, select_autoescape
import json
import re
import os
from pathlib import Path
import argparse
from more_itertools import chunked
from livereload import Server
import urllib.parse


JSON_FILEPATH = 'books.json'
IMAGE_DIR = '/images/'
BOOK_DIR = '/books/'
PAGE_DIR = '/pages/'


def get_txt_url(book_url, book_title):
    book_id = re.sub(r'[^\d*]', '', book_url)
    filename = re.sub(r'[^\w\d\. ]', '', f'{book_id}. {book_title}')
    filepath = os.path.join(BOOK_DIR, f'{filename}.txt')
    return urllib.parse.quote(filepath)


def load_books_from_json(filepath):
    with open(filepath, "r") as books_file:
        books_json = books_file.read()
    books = [[re.sub(r'^.*/', IMAGE_DIR, book['img_src']),
              book['title'], book['author'],
              get_txt_url(book['file_url'], book['title'])]
             for book in json.loads(books_json)]
    return books


def render_template(json_filepath):
    env = Environment(loader=FileSystemLoader('.'),
                      autoescape=select_autoescape(['html', 'xml']))
    template = env.get_template('template.html')

    all_books = load_books_from_json(json_filepath)
    for i, page_books in enumerate(list(chunked(all_books, 10)), 1):
        rendered_page = template.render(books=list(chunked(page_books, 2)),)
        filepath = Path(os.getcwd()+PAGE_DIR)/f'index{i}.html'
        with open(filepath, 'w', encoding="utf8") as file:
            file.write(rendered_page)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Укажите имя JSON файла с данными'
    )
    parser.add_argument(
        'filepath', help="Путь и название файла",
        default=JSON_FILEPATH, nargs='?',
    )
    args = parser.parse_args()
    books_filepath = args.filepath
    Path(os.getcwd()+PAGE_DIR).mkdir(parents=True, exist_ok=True)
    print(Path(os.getcwd()+PAGE_DIR))
    render_template(books_filepath)

    server = Server()
    server.watch('./template.html', lambda: render_template(books_filepath))
    server.serve(port=8000, default_filename='index.html',)
