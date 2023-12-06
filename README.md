# Парсер книг с сайта

Программа позволяет скачивать книги с обложками с сайта [tululu.org](https://tululu.org).

Обложки книг записываются в папку `images`.
Сами книги записываются в папку `books`.

## Установка

Для запуска скрипта необходим Python3.10+ версии и библиотеки из файла `requirements.txt`.

Установить зависимости можно командой:

```sh
pip install -r requirements.txt
```

## Запуск

Запускается командой:

```sh
python parsing.py [-h] [--start_id START_ID] [--end_id END_ID]
```

Программа имеет два аргумента:

`--start_id` - необязательный аргумент, определяет, с какой страницы начинать скачивание книг (по умолчанию 1).
`--end_id` - необязательный аргумент, определяет, до какой страницы (включительно) будут скачиваться книги (по умолчанию 10).

## Цель проекта

Код написан в образовательных целях на [онлайн-курсе для веб-разработчиков](https://dvmn.org).