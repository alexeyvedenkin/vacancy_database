# from typing import Any


class Employers():
    """ Определяет параметры для подбора работодателей с API-сервиса api.hh.ru """

    def __init__(self, data: dict) -> None:
        self.__employer_id: int = data.get('employer_id')
        self.__name: str = data.get('name')
        # self.__town: str = data.get('area', {}).get('name', '')
        self.__open_vacancies: int = data.get('open_vacancies')

    def __str__(self) -> str:
        """ Возвращает формат для вывода строкового значения работодателя """
        return (f"{self.__name.strip()}, код {self.__employer_id}, количество вакансий: {self.__open_vacancies}")
                # f"{self.__alternate_url.strip()}\n"
                # f"Описание вакансии: {self.__description.strip():<100}\n"
                # f"Требования к вакансии: {self.__requirement.strip():<100}\n\n")

    @property
    def name(self) -> str:
        """ Разрешает доступ к атрибуту name """
        return self.__name

    @property
    def open_vacancies(self) -> int:
        """ Разрешает доступ к атрибуту open_vacancies """
        return self.__open_vacancies

    @classmethod
    def from_list(cls, data_list: list) -> list:
        """ Формирует список работодателей, удовлетворяющих требованиям"""
        unique_employers = {}
        employers_list = []
        for data in data_list:
            if isinstance(data, dict):
                employers_id = data.get('employers_id')
                if employers_id not in unique_employers:
                    unique_employers[employers_id] = cls(data)
                    employers_list.append(unique_employers[employers_id])
        return employers_list
