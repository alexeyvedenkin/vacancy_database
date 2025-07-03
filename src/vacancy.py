class Vacancy:
    """ Предназначен для определения формата отображения вакансий """
    def __init__(self, name: str, employer_id: int, employer_name: str, url:str, salary_range: str) -> None:
        self.name = name
        self.employer_id = employer_id
        self.employer_name = employer_name
        self.url = url
        self.salary_range = salary_range

    def __str__(self) -> str:
        """ Форматирует представление вакансии при выводе """
        return (f"Вакансия: {self.name}\n"
                f"Работодатель: {self.employer_name} (ID: {self.employer_id})\n"
                f"URL: {self.url}\n"
                f"Зарплата: {self.salary_range}\n"
                "-------------------------")  # Добавлена линия разграничения
