import os
import requests


BOOK_DIR = 'books'

if __name__ == "__main__":
    os.makedirs(BOOK_DIR)
    url = 'https://tululu.org/txt.php'
    for id in range(1,11):
        params = {"id": id, }

        res = requests.get(url, params=params,)
        res.raise_for_status()

        filename = f'{BOOK_DIR}/book{id:02d}.txt'
        with open(filename, 'wb') as file:
            file.write(res.content)
