from http.server import HTTPServer, SimpleHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader, select_autoescape
import json
import re
import argparse


FILEPATH = 'books.json'
IMAGE_DIR = 'images/'


def load_books_from_json(filepath):
    with open(filepath, "r") as books_file:
        books_json = books_file.read()
    books = [[re.sub(r'^.*/', IMAGE_DIR, book['img_src']),
              book['title'], book['author']]
             for book in json.loads(books_json)]
    return books


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Укажите имя JSON файла с данными'
    )
    parser.add_argument(
        'filepath', help="Путь и название файла",
        default=FILEPATH, nargs='?',
    )
    args = parser.parse_args()
    books_filepath = args.filepath

    env = Environment(loader=FileSystemLoader('.'),
                      autoescape=select_autoescape(['html', 'xml']))

    template = env.get_template('template.html')

    rendered_page = template.render(
        books=load_books_from_json(books_filepath),
    )

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)

    server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
    server.serve_forever()
