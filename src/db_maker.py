import json
import os
import psycopg2
from dotenv import load_dotenv
from alt_utils import HHAPI
from src.utils import get_all_vacancies

load_dotenv()

class DBMaker:
    """ Предназначен для формирования таблиц в базе данных и их заполнения """
    def __init__(self, db_name):
        try:
            dsn = (f"dbname={db_name} user={os.getenv('USER')} password={os.getenv('PASSWORD')} "
                   f"host={os.getenv('HOST', 'localhost')} port={os.getenv('PORT', '5432')}")
            self.connection = psycopg2.connect(dsn)
            self.cursor = self.connection.cursor()
        except Exception as e:
            print("Ошибка при подключении к базе данных:", str(e))
            self.cursor = None

    def create_table(self, table_name, json_data):
        """ Формирует и заполняет таблицу на основе имеющихся данных """
        if self.cursor is None:
            print("Ошибка создания таблицы: нет соединения с базой данных.")
            return

        drop_table_query = f"DROP TABLE IF EXISTS {table_name}"
        self.cursor.execute(drop_table_query)

        # Загружаем данные из JSON
        records = json.loads(json_data)
        if isinstance(records, dict):
            records = [records]

        # Замена значений [null]
        for record in records:
            for key in record:
                if record[key] is None:
                    record[key] = 0

        # Задаем корректные типы столбцов
        columns = []
        for key in records[0].keys():
            col_type = "VARCHAR"  # По умолчанию для строковых данных
            for record in records:
                value = record[key]
                if isinstance(value, int):
                    col_type = "INT"  # Для целочисленных значений
                    break
                elif isinstance(value, float):
                    col_type = "FLOAT"  # Для чисел с плавающей точкой
                    break

            columns.append(f"{key} {col_type}")

        # Создаем таблицу с заданными наименованиями и типами столбцов
        columns_definition = ', '.join(columns)
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_definition})"
        self.cursor.execute(create_table_query)

        # Загружаем данные в таблицу
        for record in records:
            placeholders = ', '.join(['%s'] * len(record))
            insert_query = f"INSERT INTO {table_name} ({', '.join(record.keys())}) VALUES ({placeholders})"
            try:
                self.cursor.execute(insert_query, tuple(record.values()))
            except Exception as e:
                print("Ошибка при вставке данных:", str(e))

        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()

if __name__ == '__main__':
    db = DBMaker("test777")

    employer_ids = [89, 80]
    hh_api = HHAPI(employer_ids)
    hh_api.fetch_all_employers_info()
    employers_json = hh_api.to_json()
    db.create_table('employers', employers_json)
    print("Table filled with data from JSON.")

    all_vacancies = []  # Создаем пустой список для всех вакансий
    for employer in employer_ids:
        all_vacancies.extend(get_all_vacancies(employer))  # Добавляем вакансии в список

    vacancies_json = json.dumps(all_vacancies, ensure_ascii=False)  # Преобразуем все вакансии в JSON
    db.create_table('vacancies', vacancies_json)
    print("Table filled with vacancies data from JSON.")

    db.close()