import json
import os

import psycopg2 # type: ignore
from dotenv import load_dotenv
from psycopg2 import sql


load_dotenv()


class DBMaker:
    """ Предназначен для создания базы данных, формирования таблиц в базе данных и их заполнения """
    def __init__(self) -> None:
        self.user = os.getenv("USER")
        self.password = os.getenv("PASSWORD")
        self.host = os.getenv("HOST")
        self.port = os.getenv("PORT")
        self.connection = psycopg2.connect(user=self.user, password=self.password, host=self.host, port=self.port)
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()
        self.db_name: str = ""
        self.connect_to_database()

    def database_exists(self, db_name: str) -> bool:
        """ Проверяет существование базы данных с введенным названием """
        cursor = self.connection.cursor()
        cursor.execute(
            sql.SQL("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s;"),
            [db_name]
        )
        exists = cursor.fetchone() is not None  # Проверка, существует ли база данных
        cursor.close()
        return exists

    def delete_database(self, db_name: str) -> None:
        """ Выполняет удаление существующей базы данных """

        # Прерываем все действующие соединения с базой данных перед ее удалением
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT pg_terminate_backend(pg_stat_activity.pid) "
                           f"FROM pg_stat_activity WHERE pg_stat_activity.datname = %s;", (db_name,))

            cursor.execute(f"DROP DATABASE {db_name};")  # Удаляем базу

    def set_database_name(self, db_name: str) -> None:
        """ Метод для установки имени базы данных """
        self.db_name = db_name

    def create_database(self, db_name:str) -> None:
        """ Выполняет создание базы данных """
        self.set_database_name(db_name)

        if self.database_exists(db_name):  # Проверка на существование
            print(f"База данных '{db_name}' уже существует.")
            return  # Выход, если база уже существует

        cursor = self.connection.cursor()
        cursor.execute(f"CREATE DATABASE {db_name};")  # Создание базы данных
        cursor.close()

        # Обновляем self.db_name
        self.db_name = db_name

        # Закрываем текущее соединение
        self.connection.close()

        # Создаем новое соединение для новой базы
        self.connection = psycopg2.connect(database=self.db_name,
                                           user=self.user,
                                           password=self.password,
                                           host=self.host,
                                           port=self.port)
        self.connection.autocommit = True

    def connect_to_database(self) -> None:
        """ Метод для подключения к базе данных """

        if not self.db_name:
            print("Ошибка: имя базы данных не задано.")
            return

        try:
            dsn = (f"dbname={self.db_name} user={self.user} password={self.password} "
                   f"host={self.host} port={self.port}")
            self.connection = psycopg2.connect(dsn)
            self.cursor = self.connection.cursor()
        except Exception as e:
            print("Ошибка при подключении к базе данных:", str(e))
            self.cursor = None

    def create_table(self, table_name: str, json_data: str) -> None:
        """ Создает таблицы в базе данных """

        self.connect_to_database()
        if not self.cursor:
            print("Не удалось создать курсор. Прекращение.")
            return

        if isinstance(json_data, str):
            json_data = json.loads(json_data)

        # Если json_data — список, берём первый элемент для определения полей
        if isinstance(json_data, list) and json_data:
            first_row = json_data[0]
            columns = []
            for column_name, value in first_row.items():
                # Определяем типы данных для PostgreSQL
                if isinstance(value, int):
                    pg_type = "INT"
                elif isinstance(value, float):
                    pg_type = "FLOAT"
                else:
                    pg_type = "VARCHAR"
                columns.append(f'"{column_name}" {pg_type}')  # Задаем наименования и типы столбцов

        else:
            print("Ошибка: json_data должен быть непустым списком или словарём.")
            return

        # Prepare column definitions from json_data
        columns_definition = ', '.join(columns)
        create_statement = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_definition});'

        try:
            self.cursor.execute(create_statement)
            self.connection.commit()
        except Exception as e:
            print("Ошибка создания таблицы:", e)
        finally:
            self.cursor.close()
            self.connection.close()

    def fill_table(self, table_name: str, json_data: str) -> None:
        """ Выполняет загрузку данных из JSON в таблицы"""

        if isinstance(json_data, str):
            json_data = json.loads(json_data)

        if not isinstance(json_data, list):
            print("Ошибка: json-данные должны быть списком словарей.")
            return

        try:
            conn = psycopg2.connect(dbname=self.db_name, host=self.host, user=self.user, password=self.password)
            cursor = conn.cursor()

            for entry in json_data:
                if not isinstance(entry, dict):
                    print("Ошибка: каждая запись в списке должна быть словарем.")
                    continue

                # Замена значений [null] на 0
                for key in entry:
                    if entry[key] is None:
                        entry[key] = 0

                # Загрузка данных через SQL-запрос
                cursor.execute(sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(sql.Identifier(key) for key in entry.keys()),
                    sql.SQL(', ').join(sql.Placeholder() for _ in entry)
                ), tuple(entry.values()))

            conn.commit()
            print(f"Таблица {table_name} заполнена.")

        except Exception as e:
            print(f"Ошибка заполнения таблицы: {e}")
        finally:
            cursor.close()
            conn.close()

    def close(self) -> None:
        self.cursor.close()
        self.connection.close()
