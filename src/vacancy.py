class Vacancy:

    def __init__(self, name, employer_id, employer_name, url, salary_range):
        self.name = name
        self.employer_id = employer_id
        self.employer_name = employer_name
        self.url = url
        self.salary_range = salary_range

    def __str__(self):
        """ Форматирует представление вакансии при выводе """
        return (f"Вакансия: {self.name}\n"
                f"Работодатель: {self.employer_name} (ID: {self.employer_id})\n"
                f"URL: {self.url}\n"
                f"Зарплата: {self.salary_range}\n"
                "-------------------------")  # Добавлена линия разграничения
