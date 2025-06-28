class Employers():
    """ Определяет параметры для подбора работодателей с API-сервиса api.hh.ru """

    def __init__(self, data: dict) -> None:
        self.employer_id: int = data.get('employer_id')
        self.name: str = data.get('name')
        self.open_vacancies: int = data.get('open_vacancies')

    def __str__(self) -> str:
        """ Возвращает формат для вывода строкового значения работодателя """
        name = self.name.strip() if self.name else "Без названия"
        return (f"{self.employer_id}, {name}, количество вакансий: {self.open_vacancies}")

    @classmethod
    def from_list(cls, data_list: list) -> list:
        """ Формирует список работодателей, удовлетворяющих требованиям"""
        unique_employers = {}
        employers_list = []
        for data in data_list:
            if isinstance(data, dict):
                employer_id = data.get('employer_id')
                if employer_id not in unique_employers:
                    unique_employers[employer_id] = cls(data)
                    employers_list.append(unique_employers[employer_id])
        return employers_list
