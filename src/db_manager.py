import csv
import os

import psycopg2
from dotenv import load_dotenv

from config import DATA_DIR
from src.employers import Employers
from src.vacancy import Vacancy

load_dotenv()


class DBManager:
    def __init__(self, dbname):
        # Initialize the database connection
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=os.getenv('USER'),  # Pass the user parameter directly
            password=os.getenv('PASSWORD'),  # Pass the password parameter directly
            host=os.getenv('HOST'),  # Pass the host parameter directly
            port=os.getenv('PORT')  # Pass the port parameter directly
        )
        self.cursor = self.conn.cursor()

    def fetch_columns(self, table_name):
        # Запрос для получения названий и типов столбцов
        query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public';
        """
        self.cursor.execute(query, (table_name,))  # Используем параметризацию
        return self.cursor.fetchall()  # Возвращаем все результаты

    def get_companies_and_vacancies_count(self):
        # Измененный запрос для получения имени работодателя и количества вакансий
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

    def get_all_vacancies(self, limit=None):
        self.cursor.execute("""
            SELECT v.name AS vacancy_name, e.id AS employer_id, e.name AS employer_name,
                   v.alternate_url, v.salary_from, v.salary_to
            FROM vacancies v
            JOIN employers e ON v.id_employer::text = e.id::text;  -- Cast both IDs to text
        """)
        results = self.cursor.fetchall()

        # Convert results to a list of Vacancy objects
        vacancies_list = []
        for row in results:
            vacancy_name = row[0]
            employer_id = row[1]
            employer_name = row[2]
            url = row[3]
            salary_from = row[4] if row[4] else 0  # Handle None
            salary_to = row[5] if row[5] else 0  # Handle None
            salary_range = f"{salary_from} - {salary_to}"

            # Create a Vacancy object
            vacancy = Vacancy(vacancy_name, employer_id, employer_name, url, salary_range)
            vacancies_list.append(vacancy)

        # Write results to CSV (modify this method to handle Vacancy objects as needed)
        self.write_to_csv('all_vacancies.csv', vacancies_list)

        return vacancies_list  # Return the list of Vacancy objects

    def get_avg_salary(self):
        # Calculate the average salary using SQL's AVG function with updated logic
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

    def get_vacancies_with_higher_salary(self):
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

    def get_vacancies_with_keyword(self, keyword):
        self.cursor.execute("""
            SELECT v.name AS vacancy_name, e.id AS employer_id, e.name AS employer_name,
                   v.alternate_url, v.salary_from, v.salary_to
            FROM vacancies v
            JOIN employers e ON v.id_employer::text = e.id::text
            WHERE v.name ILIKE %s;  -- Added filtering in the join query
        """, (f'%{keyword}%',))
        results = self.cursor.fetchall()

        # Convert results to a list of Vacancy objects
        vacancies_list = []
        for row in results:
            vacancy_name = row[0]
            employer_id = row[1]
            employer_name = row[2]
            url = row[3]
            salary_from = row[4] if row[4] else 0  # Handle None
            salary_to = row[5] if row[5] else 0  # Handle None
            salary_range = f"{salary_from} - {salary_to}"

            # Create a Vacancy object
            vacancy = Vacancy(vacancy_name, employer_id, employer_name, url, salary_range)
            vacancies_list.append(vacancy)

        # Write results to CSV
        self.write_to_csv(f'vacancies_with_{keyword}.csv', vacancies_list)
        return vacancies_list  # Return the list of Vacancy objects

    def write_to_csv(self, filename, data):
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['name', 'employer_name', 'alternate_url', 'salary_from', 'salary_to'])  # Changed header

            for vacancy in data:
                writer.writerow([
                    vacancy.name,  # Name of the vacancy
                    vacancy.employer_name,  # Use employer_name instead of employer_id
                    vacancy.url,  # URL of the vacancy
                    vacancy.salary_range.split(" - ")[0],  # Salary From
                    vacancy.salary_range.split(" - ")[1]  # Salary To
                ])

    def display_vacancies(vacancies_list, limit=None):
        print(f"{'Employer':<30} {'Job Title':<30} {'Salary Range':<20} {'URL'}")
        print("-" * 100)  # Separator line

        # Use slicing to limit the number of vacancies displayed
        for vacancy in vacancies_list[:limit] if limit else vacancies_list:
            print(
                f"{vacancy['employer_name']:<30} {vacancy['vacancy_name']:<30} "
                f"{vacancy['salary_range']:<20} {vacancy['url']}"
            )

    def close(self):
        # Close the database connection
        self.cursor.close()
        self.conn.close()


if __name__ == '__main__':
    db_manager = DBManager('test333')  # Создание экземпляра DBManager

    # employers_columns = db_manager.fetch_columns('employers')
    # vacancies_columns = db_manager.fetch_columns('vacancies')
    #
    # # Печать результатов
    # print("Columns in 'employers':")
    # for column in employers_columns:
    #     print(column)
    #
    # print("\nColumns in 'vacancies':")
    # for column in vacancies_columns:
    #     print(column)

    try:
        mode_input = input("Выберите режим отображения (1 - Полный, любой другой символ - Облегченный): ").strip()

        # Determine the mode based on the input
        if mode_input == '1':
            mode = 'полный'  # Set mode to full if user inputs '1'
        else:
            mode = 'облегченный'  # Otherwise, set mode to simplified

        # Determine the number of vacancies to show in Simplified mode
        if mode == 'облегченный':
            count = int(input("Введите количество вакансий для вывода: "))  # User input for count
        else:
            count = None  # Show all vacancies in Full mode

        # Print the selected mode and count for confirmation - optional
        print(f"Выбранный режим: {mode}")
        if count is not None:
            print(f"Количество вакансий для вывода: {count}")

        # Display information about employers and open vacancies
        print("Сведения о работодателях и количестве открытых вакансий:")
        info_from_company_and_vacancies = db_manager.get_companies_and_vacancies_count()
        print(f"{'ID':<10} {'Company Name':<60} {'Open Vacancies':<10}")
        print("-" * 80)  # Separator line

        for employer in info_from_company_and_vacancies:
            employer_id = getattr(employer, 'employer_id', 'N/A')
            employer_name = getattr(employer, 'name', 'Unknown Company')
            vacancies_count = getattr(employer, 'open_vacancies', 0)
            print(f"{employer_id:<10} {employer_name:<60} {vacancies_count:<10}")

        print()  # Print a new line

        # Wait for the user to proceed to the next block of data
        input("Нажмите Enter, чтобы перейти к сведениям об открытых вакансиях...")

        print("Сведения об открытых вакансиях")
        vacancies = db_manager.get_all_vacancies()  # Call the method to get the vacancies

        # Use user-defined count or default to 5 if count is None (Full mode)
        for vacancy in vacancies[:count] if count is not None else vacancies:
            print(vacancy)  # Print the formatted Vacancy

        print()
        print(f'Выведены сведения о {len(vacancies[:count])} вакансий из имеющихся {len(vacancies)}')
        print('Полный список вакансий выгружен в файл "data/all_vacancies.csv"')
        print()

        # Wait for the user to proceed to the Average Salary section
        input("Нажмите Enter, чтобы перейти к средней зарплате...")

        avg_salary = db_manager.get_avg_salary()
        print(f'Средняя зарплата по отобранным вакансиям: {round(avg_salary, 2)}')
        print()

        input("Нажмите Enter, чтобы перейти к вакансиям с зарплатой выше средней...")
        # Higher salary vacancies
        print("Сведения о вакансиях с зарплатой выше средней")
        higher_vacancies = db_manager.get_vacancies_with_higher_salary()
        for vacancy in higher_vacancies[:count] if count is not None else higher_vacancies:
            print(vacancy)

        print()
        print(f'Выведены сведения о {len(higher_vacancies[:count])} вакансий из имеющихся {len(higher_vacancies)}')
        print('Полный список вакансий выгружен в файл "data/higher_salary_vacancies.csv"')
        print()

        # Wait for the user to continue to filtering vacancies
        input("Нажмите Enter, чтобы перейти к фильтрации вакансий...")

        # Filtering vacancies with the keyword
        user_key = input('Введите ключевое слово для фильтрации вакансий:')
        print()
        filtered_vacancies = db_manager.get_vacancies_with_keyword(user_key)
        for vacancy in filtered_vacancies[:count] if count is not None else filtered_vacancies:
            print(vacancy)
        print(f'Выведены сведения о {len(filtered_vacancies[:count])} вакансий из имеющихся {len(filtered_vacancies)}')
        print(f'Полный список вакансий выгружен в файл "data/vacancies_with_{user_key}.csv"')

    except Exception as e:
        print(f'Ошибка при извлечении данных: {e}')

    db_manager.close()
