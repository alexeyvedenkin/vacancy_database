import json
import psycopg2
from dotenv import load_dotenv
from src.hh_api import HHAPI
import os
from src.utils_alt3 import get_all_vacancies


class DBMaker:
    def __init__(self):
        load_dotenv()
        self.user = os.getenv('USER')
        self.password = os.getenv('PASSWORD')
        self.host = os.getenv('HOST', 'localhost')
        self.port = os.getenv('PORT', '5432')
        self.dbname = self.get_database_name()
        self.conn = None

    @staticmethod
    def get_database_name():
        return input("Введите название базы данных: ")

    def create_database(self):
        # Connect to the postgres database with autocommit mode set to True
        conn = psycopg2.connect(dbname='postgres', user=self.user, password=self.password,
                                host=self.host, port=self.port)
        conn.autocommit = True  # Set autocommit to True for database creation
        with conn.cursor() as cur:  # Using context manager for cursor
            cur.execute(f'CREATE DATABASE {self.dbname};')
        conn.close()  # Close the connection after use

    def create_table(self, table_name, columns):
        with psycopg2.connect(dbname=self.dbname, user=self.user, password=self.password,
                              host=self.host, port=self.port) as conn:
            with conn.cursor() as cur:  # Using context manager for cursor
                column_defs = ', '.join(f"{col} VARCHAR(25)" for col in columns)
                cur.execute(f'CREATE TABLE {table_name} ({column_defs});')
                conn.commit()

    def fill_table_from_json(self, table_name, json_data):
        if isinstance(json_data, str):
            json_data = json.loads(json_data)

        if not json_data:  # Check for empty json_data
            print("No data to insert.")
            return

        columns = list(json_data[0].keys())
        with psycopg2.connect(dbname=self.dbname, user=self.user,
                              password=self.password, host=self.host, port=self.port) as conn:
            with conn.cursor() as cur:  # Using context manager for cursor
                for entry in json_data:
                    values = [entry.get(column, None) for column in columns]
                    placeholders = ', '.join(['%s'] * len(columns))
                    cur.execute(f'''
                        INSERT INTO {table_name} ({', '.join(columns)}) 
                        VALUES ({placeholders});
                    ''', values)
                conn.commit()  # Commit after all insertions


if __name__ == "__main__":
    db_maker = DBMaker()

    # Create the database
    db_maker.create_database()
    print(f"Database '{db_maker.dbname}' created.")

    # Create Employers Table
    table_name = 'employers'
    columns = ['id', 'name', 'open_vacancies']
    db_maker.create_table(table_name, columns)
    print(f"Таблица '{table_name}' сформирована со столбцами {columns}.")

    # Fetch Employers Data
    employer_ids = [89]  # Example IDs
    hh_api = HHAPI(employer_ids)
    hh_api.fetch_all_employers_info()
    json_data = hh_api.to_json()  # Serialize employers to JSON
    db_maker.fill_table_from_json(table_name, json_data)
    print("Table filled with data from JSON.")

    # Create Vacancies Table
    table_name = 'vacancies'
    columns = ['employer_id', 'name', 'salary_from', 'salary_to']
    db_maker.create_table(table_name, columns)
    print(f"Таблица '{table_name}' сформирована со столбцами {columns}.")

    for employer in employer_ids:
        all_vacancies = get_all_vacancies(employer)
        vacancies_json = json.dumps(all_vacancies, ensure_ascii=False)
        db_maker.fill_table_from_json(table_name, vacancies_json)  # Use vacancies_json here
        print("Table filled with vacancies data from JSON.")