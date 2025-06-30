import requests
import psycopg2
import json
import os
from dotenv import load_dotenv
from config import DATA_DIR


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


def get_employers_with_vacancies(min_vacancies):
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


def get_all_vacancies(employer_id):
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


def export_tables_to_json(dbname):
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


def load_fixtures(db_maker) -> None:
    """Загружает данные из JSON-файлов в директории 'data/fixtures'."""

    fixtures_dir = os.path.join(DATA_DIR, 'fixtures')  # Use DATA_DIR for the correct path

    # Check if the fixtures directory exists
    if not os.path.exists(fixtures_dir):
        print(f"The directory {fixtures_dir} does not exist.")
        return  # Exit if directory is not found

    for filename in os.listdir(fixtures_dir):
        if filename.endswith('.json'):
            # Используем try-except для обработки возможных ошибок при открытии файла
            try:
                with open(os.path.join(fixtures_dir, filename), 'r', encoding='utf-8') as file:
                    json_data = json.load(file)  # Загружаем данные из JSON файла
                    db_maker.create_table(filename[:-5], json_data)  # Создаем таблицу по имени файла без расширения
                    db_maker.fill_table(filename[:-5], json_data)  # Заполняем таблицу данными
                    print(f"Загружены данные из '{filename}' в таблицу '{filename[:-5]}'.")
            except Exception as e:
                print(f"Ошибка при загрузке файла '{filename}': {e}")  # Выводим сообщение об ошибке
