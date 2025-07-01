import json
from typing import Any, Optional

import requests # type: ignore


class Employer:
    """ Определяет параметры экземпляра работодателя """

    def __init__(self, employer_id: int, employer_name: str, vacancies_url: str, open_vacancies_count: int) -> None:
        self.employer_id = employer_id  # Сохраняем ID работодателя
        self.employer_name = employer_name  # Сохраняем наименование работодателя
        self.vacancies_url = vacancies_url  # Ссылка на открытые вакансии
        self.open_vacancies_count = open_vacancies_count  # Количество открытых вакансий

    def to_dict(self) -> dict:
        """ Преобразует объект класса Employer в словарь """
        return {
            'id': self.employer_id,
            'name': self.employer_name,
            'open_vacancies': self.open_vacancies_count
        }


class HHAPI:
    """ Вспомогательный класс для предварительного отбора работодателей """

    def __init__(self, employer_ids: list) -> None:
        self.employer_ids = employer_ids
        self.employers: list[Employer] = []

    def fetch_employer_info(self, employer_id: int) -> Optional[Employer]:
        """ Получает информацию о работодателе с сервиса api.hh.ru по его ID """

        response = requests.get(f'https://api.hh.ru/employers/{employer_id}')
        if response.status_code == 200:
            data = response.json()
            employer = Employer(
                employer_id=data['id'],
                employer_name=data['name'],
                vacancies_url=data['vacancies_url'],
                open_vacancies_count=data['open_vacancies']
            )
            return employer

        else:
            print(f"Ошибка получения данных для работодателя {employer_id}")
            return None

    def fetch_all_employers_info(self) -> None:
        """ Объединяет в список информацию о нескольких работодателях """
        for employer_id in self.employer_ids:
            employer = self.fetch_employer_info(employer_id)
            if employer:
                self.employers.append(employer)

    def to_json(self) -> str:
        """ Выгружает в JSON информацию из списка работодателей """
        return json.dumps([employer.to_dict() for employer in self.employers], ensure_ascii=False)

    def fetch_vacancies_by_employer_id(self, employer_id: int) -> Any:
        """ Возвращает ссылку на открытые вакансии работодателя """
        employer = next((e for e in self.employers if e.employer_id == employer_id), None)
        if employer:
            response = requests.get(employer.vacancies_url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка получения вакансий для работодателя {employer_id}")
                return None
        else:
            print(f"Работодатель с ID {employer_id} не найден в списке.")
            return None

# Пример использования:
if __name__ == "__main__":
    employer_ids = [80, 89]  # Замените на реальные ID работодателей
    hh_api = HHAPI(employer_ids)
    hh_api.fetch_all_employers_info()

    for employer in hh_api.employers:
        print(f"Работодатель ID: {employer.employer_id}, Name: {employer.employer_name}, "
              f"Открыто вакансий: {employer.open_vacancies_count}, Ссылка: {employer.vacancies_url}")
