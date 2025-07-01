import json
import os

import psycopg2 # type: ignore
import requests # type: ignore
from dotenv import load_dotenv

from config import DATA_DIR
from src.db_maker import DBMaker

load_dotenv()


def get_employer_id(employer_name: str) -> None:
    """ Вспомогательная функция для определения ID работодателя по его наименованию """
    url = "https://api.hh.ru/employers"
    params = {'text': employer_name, 'area': 113}

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        found = False
        if data and 'items' in data:
            for employer in data['items']:
                if employer_name.lower() in employer['name'].lower():
                    found = True
                    print(f"ID: {employer['id']},"
                          f" Name: {employer['name']}, "
                          f"Открыто вакансий: {employer['open_vacancies']}")
            if not found:
                print("Работодатель не найден.")
        else:
            print("Работодатель не найден.")
    else:
        print("Ошибка при запросе:", response.status_code)


def get_employers_with_vacancies(min_vacancies: int) -> None:
    """ Вспомогательная функция для подбора работодателя по необходимому количеству вакансий """
    url = "https://api.hh.ru/employers"
    params = {'open_vacancies': min_vacancies}  # Задан фильтр по минимально необходимому количеству вакансий
    response = requests.get(url, params=params)

    if response.status_code == 200:
        employers = response.json()
        found = False
        if 'items' in employers:
            for employer in employers['items']:
                # Проверка количества вакансий на соответствие критерию
                if employer['open_vacancies'] >= min_vacancies:
                    found = True
                    print(f"Работодатель: {employer['name']}, Вакансий: {employer['open_vacancies']}")
        if not found:
            print("Не найдено работодателей с количеством вакансий", min_vacancies, "и более.")
    else:
        print("Ошибка при запросе:", response.status_code)


def get_all_vacancies(employer_id: int) -> list:
    """ Функция для получения всех вакансий работодателя """
    vacancies = []
    page = 0

    while True:
        url = f'https://api.hh.ru/vacancies?employer_id={employer_id}&page={page}'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])

            if not items:
                break

            for item in items:
                try:
                    vacancy = {
                        'vacancy_id': item.get('id'),
                        'name': item.get('name'),
                        'id_employer': employer_id,
                        'alternate_url': item.get('alternate_url'),
                        'salary_from': item['salary']['from'] if item['salary'] else 0,
                        'salary_to': item['salary']['to'] if item['salary'] else 0
                    }
                    vacancies.append(vacancy)
                except KeyError:
                    print(f'Ошибка с вакансией: {item.get("id")}, пропускаем.')

            page += 1
        elif response.status_code == 403:
            print(f'Ошибка 403 для работодателя {employer_id}: доступ запрещён. Пропускаем. ')  # Print the 403 error
            break
        else:
            print(f'Ошибка: {response.status_code}')
            break

    return vacancies


def export_tables_to_json(dbname: str) -> None:
    """ Загружает фикстуры таблиц из базы данных """

    # Создание соединения с базой данных
    conn = psycopg2.connect(
        dbname='postgres',
        user=os.getenv('USER'),
        password=os.getenv('PASSWORD'),
        host=os.getenv('HOST'),
        port=os.getenv('PORT')
    )

    # Получение курсора
    cur = conn.cursor()

    # Получение имен таблиц
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cur.fetchall()

    # Создание директории для JSON-файлов в data/fixtures
    output_dir = os.path.join(DATA_DIR, 'fixtures')  # Конструируем путь
    os.makedirs(output_dir, exist_ok=True)  # Создает папку, если не существует

    # Получение данных для каждой таблицы и запись в файлы JSON
    for table in tables:
        table_name = table[0]

        # Получаем данные из таблицы
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()

        # Получаем имена колонок
        colnames = [desc[0] for desc in cur.description]

        # Создание списка словарей для фикстур
        fixtures = [dict(zip(colnames, row)) for row in rows]

        # Сохранение в JSON-файл
        with open(os.path.join(output_dir, f"{table_name}.json"), 'w', encoding='utf-8') as json_file:
            json.dump(fixtures, json_file, ensure_ascii=False, indent=4)

    # Закрытие курсора и соединения
    cur.close()
    conn.close()

    print("Фикстуры успешно сохранены в папку 'data/fixtures'.")


def load_fixtures(db_maker: DBMaker) -> None:
    """Загружает данные из JSON-файлов в директории 'data/fixtures'."""

    fixtures_dir = os.path.join(DATA_DIR, 'fixtures')  # Use DATA_DIR for the correct path

    # Check if the fixtures directory exists
    if not os.path.exists(fixtures_dir):
        print(f"Директория {fixtures_dir} не существует.")
        return  # Exit if directory is not found

    for filename in os.listdir(fixtures_dir):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(fixtures_dir, filename), 'r', encoding='utf-8') as file:
                    json_data = json.load(file)  # Load data from JSON file

                    table_name = filename[:-5]  # Get the table name without the ".json" extension

                    # Check existence and create table
                    db_maker.create_table(table_name, json_data)  # Create table
                    print(f"Table '{table_name}' created (if it didn't exist).")

                    db_maker.fill_table(table_name, json_data)  # Fill the table with data
                    print(f"Загружены данные из '{filename}' в таблицу '{table_name}'.")
            except Exception as e:
                print(f"Ошибка при загрузке файла '{filename}': {e}")  # Output error message
