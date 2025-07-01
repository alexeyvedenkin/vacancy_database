import json
import os
import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

from src.hh_api import HHAPI
from src.utils import get_all_vacancies

load_dotenv()

class DBMaker:
    """ Предназначен для создания базы данных, формирования таблиц в базе данных и их заполнения """
    def __init__(self):
        self.user = os.getenv("USER")
        self.password = os.getenv("PASSWORD")
        self.host = os.getenv("HOST")
        self.port = os.getenv("PORT")
        self.connection = psycopg2.connect(user=self.user, password=self.password, host=self.host, port=self.port)
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()
        self.db_name = None
        self.connect_to_database()

    def database_exists(self, db_name):
        cursor = self.connection.cursor()
        cursor.execute(
            sql.SQL("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s;"),
            [db_name]
        )
        exists = cursor.fetchone() is not None  # Проверка, существует ли база данных
        cursor.close()
        return exists

    def delete_database(self, db_name):
        # Terminate the connections to the database before dropping it
        with self.connection.cursor() as cursor:
            cursor.execute(f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = %s;", (db_name,))
            cursor.execute(f"DROP DATABASE {db_name};")  # Now drop the database

    def create_database(self, db_name):
        if self.database_exists(db_name):  # Проверка на существование
            print(f"База данных '{db_name}' уже существует.")
            return  # Выход, если база уже существует

        cursor = self.connection.cursor()
        cursor.execute(f"CREATE DATABASE {db_name};")  # Создание базы данных
        cursor.close()

        # Закрываем текущее соединение
        self.connection.close()

        # Создаем новое соединение для новой базы
        self.connection = psycopg2.connect(database=db_name,
                                           user=self.user,
                                           password=self.password,
                                           host=self.host,
                                           port=self.port) # обращаем внимание на параметры
        self.connection.autocommit = True  # Включение автокоммита

    def connect_to_database(self):
        """ Метод для подключения к базе данных """

        try:
            dsn = (f"dbname={self.db_name} user={self.user} password={self.password} "
                   f"host={self.host} port={self.port}")
            self.connection = psycopg2.connect(dsn)  # Connect to the new database
            self.cursor = self.connection.cursor()
        except Exception as e:
            print("Ошибка при подключении к базе данных:", str(e))
            self.cursor = None

        if not self.db_name:
            print("Ошибка: имя базы данных не задано.")
            return

    def create_table(self, table_name, json_data):  # Added 'self' to parameters
        self.connect_to_database()  # Call the method to connect to the database
        if not self.cursor:  # Check if cursor created successfully
            print("Не удалось создать курсор. Прекращение.")
            return

        # Если json_data — список, берём первый элемент для определения полей
        if isinstance(json_data, list) and json_data:  # Ensure json_data is a non-empty list
            first_row = json_data[0]
            columns = []
            for column_name, value in first_row.items():
                # Determine the data type for PostgreSQL
                if isinstance(value, int):
                    pg_type = "INT"  # Change INTEGER to INT
                elif isinstance(value, float):
                    pg_type = "FLOAT"  # Change REAL to FLOAT
                else:
                    pg_type = "VARCHAR"  # Change TEXT to VARCHAR by default
                columns.append(f'"{column_name}" {pg_type}')  # Append the column definition

        else:
            print("Ошибка: json_data должен быть непустым списком или словарём.")
            return

        # Prepare column definitions from json_data
        columns_definition = ', '.join(columns)
        create_statement = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_definition});'

        try:
            # Remove the second execution; it's redundant
            self.cursor.execute(create_statement)  # Execute the create statement
            self.connection.commit()  # Save (commit) changes
        except Exception as e:
            print("Ошибка создания таблицы:", e)  # Print error if it occurs
        finally:
            self.cursor.close()  # Close cursor
            self.connection.close()  # Close connection

    def fill_table(self, table_name, json_data):
        # Ensure json_data is a list of dictionaries
        if isinstance(json_data, str):
            json_data = json.loads(json_data)  # Load string to JSON if needed

        if not isinstance(json_data, list):  # Check if json_data is a list
            print("Ошибка: json-данные должны быть списком словарей.")
            return

        try:
            conn = psycopg2.connect(dbname=self.db_name, host=self.host, user=self.user, password=self.password)
            cursor = conn.cursor()

            for entry in json_data:
                if not isinstance(entry, dict):  # Ensure each entry is a dictionary
                    print("Ошибка: каждая запись в списке должна быть словарем.")
                    continue

                # Use the table_name parameter in the SQL query
                cursor.execute(sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table_name),  # Use table_name safely
                    sql.SQL(', ').join(sql.Identifier(key) for key in entry.keys()),
                    sql.SQL(', ').join(sql.Placeholder() for _ in entry)  # Placeholders for the values
                ), tuple(entry.values()))  # Pass values here

            conn.commit()
            print(f"Таблица {table_name} заполнена.")

        except Exception as e:
            print(f"Ошибка заполнения таблицы: {e}")
        finally:
            cursor.close()
            conn.close()

    def close(self):
        self.cursor.close()
        self.connection.close()

if __name__ == '__main__':
    db = DBMaker("test999")
    user_sample_ids = [1740, 89, 15478, 9694561, 1808, 3809, 740, 909495, 1669269, 20189, 107434]
    # employer_ids = [89, 80]
    hh_api = HHAPI(user_sample_ids)
    print(111)
    hh_api.fetch_all_employers_info()
    print(222)
    employers_json = hh_api.to_json()
    print(333)
    db.create_table('employers', employers_json)
    print("Table filled with data from JSON.")

    all_vacancies = []  # Create an empty list for all vacancies
    print(444)
    for employer in user_sample_ids:
        print(555)
        try:
            # Attempt to get all vacancies for the employer
            vacancies = get_all_vacancies(employer)
            print(f'Количество вакансий у работодателя c ID={employer}: {len(vacancies)}')
            all_vacancies.extend(vacancies)  # Add vacancies to the list
            print(f'Текущее количество отобранных вакансий: {len(all_vacancies)}')
        except Exception as e:  # Catch any exception, like a 403 error
            # Print the error with ids for better traceability
            print(f"Error for employer {employer}: {e}")

    print(666)
    vacancies_json = json.dumps(all_vacancies, ensure_ascii=False)
    print(777)
    # Create table in database
    db.create_table('vacancies', vacancies_json)
    print("Table filled with vacancies data from JSON.")

    db.close()