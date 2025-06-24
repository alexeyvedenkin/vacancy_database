import psycopg2


class DBManager:
    def __init__(self, dbname, user, password, host='localhost', port='5432'):
        # Initialize the database connection
        self.connection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cursor = self.connection.cursor()

    def get_companies_and_vacancies_count(self):
        # Get a list of all companies and their vacancy counts
        query = '''
            SELECT companies.name, COUNT(vacancies.id) 
            FROM companies 
            LEFT JOIN vacancies ON companies.id = vacancies.company_id 
            GROUP BY companies.name;
        '''
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_all_vacancies(self):
        # Get a list of all vacancies with company name, job title, salary, and URL
        query = '''
            SELECT vacancies.title, companies.name, vacancies.salary_from, vacancies.salary_to, vacancies.url 
            FROM vacancies 
            JOIN companies ON vacancies.company_id = companies.id;
        '''
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_avg_salary(self):
        # Calculate the average salary based on the logic provided
        query = '''
            SELECT salary_from, salary_to FROM vacancies;
        '''
        self.cursor.execute(query)
        salaries = self.cursor.fetchall()

        total_salary, count = 0, 0

        for salary_from, salary_to in salaries:
            if salary_from > 0 and salary_to == 0:
                total_salary += salary_from
                count += 1
            elif salary_from == 0 and salary_to > 0:
                total_salary += salary_to / 2
                count += 1
            elif salary_from > 0 and salary_to > 0:
                total_salary += (salary_from + salary_to) / 2
                count += 1

        return total_salary / count if count > 0 else 0  # Return average or 0 if no valid salaries

    def get_vacancies_with_higher_salary(self):
        # Get vacancies with salaries above the average salary
        avg_salary = self.get_avg_salary()
        query = '''
            SELECT vacancies.title, companies.name, vacancies.salary_from, vacancies.salary_to 
            FROM vacancies 
            JOIN companies ON vacancies.company_id = companies.id 
            WHERE (salary_from > %s OR salary_to > %s);
        '''
        self.cursor.execute(query, (avg_salary, avg_salary))
        return self.cursor.fetchall()

    def get_vacancies_with_keyword(self, keyword):
        # Get vacancies that contain the specified keyword in their title
        query = '''
            SELECT vacancies.title, companies.name, vacancies.salary_from, vacancies.salary_to 
            FROM vacancies 
            JOIN companies ON vacancies.company_id = companies.id 
            WHERE vacancies.title ILIKE %s;
        '''
        self.cursor.execute(query, (f'%{keyword}%',))
        return self.cursor.fetchall()

    def close(self):
        # Close the database connection
        self.cursor.close()
        self.connection.close()