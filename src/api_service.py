from typing import Any

import requests # type: ignore

from config import EMPLOYERS_ID
from src.hh_api import Employer
from src.vacancy import Vacancy


class HeadHunterAPI():
    """ Класс для работы с API HeadHunter """

    def __init__(self, file_worker: Any) -> None:
        super().__init__()
        self.__headers = {'User-Agent': 'HH-User-Agent'}
        self.__params = {'text': '', 'page': 0, 'per_page': 100, 'area': 113, 'employer_id': ''}
        self.__employers: list[Employer] = []
        self.__vacancies: list[Vacancy] = []
        self.__file_worker = file_worker

    def get_employers(self) -> list:
        """ Осуществляет доступ к приватному атрибуту """
        return self.__employers

    def get_vacancies(self) -> list:
        """ Осуществляет доступ к приватному атрибуту """
        return self.__vacancies

    def load_employers(self, keyword: str) -> list:
        """ Метод для загрузки работодателей с сайта api.hh.ru """
        for employer_id in EMPLOYERS_ID:
            response = requests.get(f"{self.__url}/{employer_id}", headers=self.__headers)

            if response.status_code != 200:
                print(f"Ошибка: {response.status_code} для ID: {employer_id}")
                continue

            employer_data = response.json()

            if keyword.lower() in employer_data.get('name', '').lower():
                self.__employers.append(employer_data)

        return self.__employers

    def load_vacancies(self, employer_id: Any) -> Any:
        """ Метод для загрузки вакансий с сайта api.hh.ru """
        self.__url = 'https://api.hh.ru/vacancies'
        self.__params['employer_id'] = employer_id
        self.__params['page'] = 0
        max_pages = 50

        while self.__params['page'] < max_pages:
            response = requests.get(self.__url, headers=self.__headers, params=self.__params)

            if response.status_code != 200:
                print(f"Ошибка: {response.status_code}")
                break

            fetched_vacancies = response.json().get('items', [])

            if not fetched_vacancies:
                break

            for vacancy in fetched_vacancies:

                print(vacancy)

                salary = vacancy.get('salary')
                if salary is not None and salary.get('currency') == 'RUR':

                    if employer_id == vacancy['employer']['id']:
                        self.__vacancies.append(vacancy)

            self.__params['page'] += 1

        return self.__vacancies
