from typing import Any

import requests


class HeadHunterAPI():
    """ Класс для работы с API HeadHunter """

    def __init__(self, file_worker: Any) -> None:
        super().__init__()
        # self.__url = 'https://api.hh.ru/vacancies'
        self.__headers = {'User-Agent': 'HH-User-Agent'}
        self.__params = {'text': '', 'page': 0, 'per_page': 100, 'area': 113, 'employer_id': ''}
        self.__employers = []
        self.__vacancies = []
        self.__file_worker = file_worker

    def get_employers(self) -> list:
        """ Осуществляет доступ к приватному атрибуту """
        return self.__employers

    def get_vacancies(self) -> list:
        """ Осуществляет доступ к приватному атрибуту """
        return self.__vacancies

    def load_employers(self, keyword: Any) -> Any:
        """ Метод для загрузки работодателей с сайта api.hh.ru """
        self.__url = 'https://api.hh.ru/employers'
        self.__params['text'] = keyword
        max_pages = 50  # Устанавливаем максимальное количество страниц для 5000 результатов
        while self.__params.get('page') < max_pages:  # Проверяем, не превышает ли страница максимальную
            response = requests.get(self.__url, headers=self.__headers, params=self.__params)
            fetched_employers = response.json()['items']

            # Если нет больше работодателей, выходим из цикла
            if not fetched_employers:
                break  # Прерываем цикл, если нет данных

            for employer in fetched_employers:
                if 'employer' in employer and 'name' in employer['employer']:
                    if keyword.lower() in employer['employer']['name'].lower():
                        self.__employers.append(employer)
            self.__params['page'] += 1  # Переход к следующей странице
        return self.__employers

    def load_vacancies(self, employer_id: Any) -> Any:
        """ Метод для загрузки вакансий с сайта api.hh.ru """
        self.__url = 'https://api.hh.ru/vacancies'
        self.__params['employer_id'] = employer_id
        self.__params['page'] = 0  # Сброс страницы перед загрузкой
        max_pages = 50

        while self.__params.get('page') < max_pages:  # Проверяем количество страниц
            response = requests.get(self.__url, headers=self.__headers, params=self.__params)
            fetched_vacancies = response.json()['items']

            # Если нет больше вакансий, выходим из цикла
            if not fetched_vacancies:
                break  # Прерываем цикл, если нет данных

            for vacancy in fetched_vacancies:
                if employer_id == vacancy['employer']['id']:
                    self.__vacancies.append(vacancy)

            self.__params['page'] += 1  # Переход к следующей странице

        return self.__vacancies
