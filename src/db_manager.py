import csv
import os
from typing import Any, Optional, List, Dict

import psycopg2 # type: ignore
from dotenv import load_dotenv

from config import DATA_DIR
from src.employers import Employers
from src.vacancy import Vacancy

load_dotenv()


class DBManager:
    def __init__(self, dbname: str) -> None:
        # Initialize the database connection
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=os.getenv('USER'),  # Pass the user parameter directly
            password=os.getenv('PASSWORD'),  # Pass the password parameter directly
            host=os.getenv('HOST'),  # Pass the host parameter directly
            port=os.getenv('PORT')  # Pass the port parameter directly
        )
        self.cursor = self.conn.cursor()

    def fetch_columns(self, table_name: str) -> Any:
        """ Запрос для получения названий и типов столбцов """

        query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public';
        """
        self.cursor.execute(query, (table_name,))  # Используем параметризацию
        return self.cursor.fetchall()  # Возвращаем все результаты

    def get_companies_and_vacancies_count(self) -> list:
        """ Запрос для получения имени работодателя и количества вакансий"""

        self.cursor.execute("""
                    SELECT e.id, e.name, COUNT(v.vacancy_id)
                    FROM employers e
                    LEFT JOIN vacancies v ON e.id = v.id_employer::character varying
                    GROUP BY e.id, e.name;
                """)
        results = self.cursor.fetchall()

        employers_list = []
        for row in results:
            employer_id = row[0]
            employer_name = row[1]
            open_vacancies = row[2]

            employer = Employers({
                'employer_id': employer_id,
                'name': employer_name,
                'open_vacancies': open_vacancies
            })

            # Добавляем объект Employers в список
            employers_list.append(employer)  # Добавил объект, а не строку

        return employers_list

    def get_all_vacancies(self, limit: Optional[int] = None) -> list:
        """ Запрос для получения всех открытых вакансий работодателя """

        self.cursor.execute("""
            SELECT v.name AS vacancy_name, e.id AS employer_id, e.name AS employer_name,
                   v.alternate_url, v.salary_from, v.salary_to
            FROM vacancies v
            JOIN employers e ON v.id_employer::text = e.id::text;  -- Cast both IDs to text
        """)
        results = self.cursor.fetchall()

        # Преобразование ответа к данным, необходимым для создания экземпляра класса Vacancy
        vacancies_list = []
        for row in results:
            vacancy_name = row[0]
            employer_id = row[1]
            employer_name = row[2]
            url = row[3]
            salary_from = row[4] if row[4] else 0
            salary_to = row[5] if row[5] else 0
            salary_range = f"{salary_from} - {salary_to}"

            # Создание экземпляра класса Vacancy
            vacancy = Vacancy(vacancy_name, employer_id, employer_name, url, salary_range)
            vacancies_list.append(vacancy)

        # Записываем в файл .csv
        self.write_to_csv('all_vacancies.csv', vacancies_list)

        return vacancies_list  # Return the list of Vacancy objects

    def get_avg_salary(self) -> Any:
        """ Запрос на получение средней зарплаты с помощью функции AVG """

        query = '''
            SELECT AVG(CASE
                WHEN salary_from > 0 AND salary_to = 0 THEN salary_from
                WHEN salary_from = 0 AND salary_to > 0 THEN salary_to * 0.75
                WHEN salary_from > 0 AND salary_to > 0 THEN (salary_from + salary_to) / 2
                ELSE NULL
            END) FROM vacancies;
        '''

        self.cursor.execute(query)
        avg_salary = self.cursor.fetchone()[0]  # Fetch the result from the query

        return avg_salary if avg_salary is not None else 0

    def get_vacancies_with_higher_salary(self) -> list:
        """ Запрос для отбора вакансий с зарплатой выше средней """
        avg_salary = self.get_avg_salary()

        # Кастуем v.id_employer в текст для соответствия с e.id
        self.cursor.execute("""
            SELECT v.name AS vacancy_name, e.id AS employer_id, e.name AS employer_name,
                   v.alternate_url, v.salary_from, v.salary_to
            FROM vacancies v
            JOIN employers e ON v.id_employer::text = e.id::text  -- Кастинг типов
            WHERE (v.salary_from + v.salary_to) / 2 > %s;  -- Условие по средней зарплате
        """, (avg_salary,))

        results = self.cursor.fetchall()
        vacancies = []

        for row in results:
            vacancy_name, employer_id, employer_name, url, salary_from, salary_to = row
            salary_range = f"{salary_from} - {salary_to}"
            vacancy = Vacancy(vacancy_name, employer_id, employer_name, url, salary_range)
            vacancies.append(vacancy)

        self.write_to_csv('higher_salary_vacancies.csv', vacancies)
        return vacancies

    def get_vacancies_with_keyword(self, keyword: str) -> list:
        """ Запрос для фильтрации по ключевому слову """

        self.cursor.execute("""
            SELECT v.name AS vacancy_name, e.id AS employer_id, e.name AS employer_name,
                   v.alternate_url, v.salary_from, v.salary_to
            FROM vacancies v
            JOIN employers e ON v.id_employer::text = e.id::text
            WHERE v.name ILIKE %s;  -- Added filtering in the join query
        """, (f'%{keyword}%',))
        results = self.cursor.fetchall()

        # Преобразовываем в список экземпляров класса Vacancy
        vacancies_list = []
        for row in results:
            vacancy_name = row[0]
            employer_id = row[1]
            employer_name = row[2]
            url = row[3]
            salary_from = row[4] if row[4] else 0
            salary_to = row[5] if row[5] else 0
            salary_range = f"{salary_from} - {salary_to}"

            # Create a Vacancy object
            vacancy = Vacancy(vacancy_name, employer_id, employer_name, url, salary_range)
            vacancies_list.append(vacancy)

        # Write results to CSV
        self.write_to_csv(f'vacancies_with_{keyword}.csv', vacancies_list)
        return vacancies_list

    def write_to_csv(self, filename: str, data: list) -> None:
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['name', 'employer_name', 'alternate_url', 'salary_from', 'salary_to'])  # Changed header

            for vacancy in data:
                writer.writerow([
                    vacancy.name,
                    vacancy.employer_name,
                    vacancy.url,
                    vacancy.salary_range.split(" - ")[0],  # Salary_from
                    vacancy.salary_range.split(" - ")[1]  # Salary_to
                ])

    def display_vacancies(self, vacancies_list: List[Dict[str, str]], limit: Optional[int] = None) -> None:
        """ Отображает заданное количество отфильтрованных вакансий """

        print(f"{'Employer':<30} {'Job Title':<30} {'Salary Range':<20} {'URL'}")
        print("-" * 100)  # Добавлена линия разделения

        # Вывод вакансий с помощью среза
        for vacancy in vacancies_list[:limit] if limit else vacancies_list:
            print(
                f"{vacancy['employer_name']:<30} {vacancy['vacancy_name']:<30} "
                f"{vacancy['salary_range']:<20} {vacancy['url']}"
            )

    def close(self) -> None:
        """ Закрывает соединение с базой данных """

        self.cursor.close()
        self.conn.close()
