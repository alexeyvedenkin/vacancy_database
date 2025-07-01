import json

import requests


class Employer:
    def __init__(self, employer_id, employer_name, vacancies_url, open_vacancies_count):
        self.employer_id = employer_id  # Сохраняем ID работодателя
        self.employer_name = employer_name  # Сохраняем наименование работодателя
        self.vacancies_url = vacancies_url  # Ссылка на открытые вакансии
        self.open_vacancies_count = open_vacancies_count  # Количество открытых вакансий

    def to_dict(self):  # Method to convert Employer object to dictionary
        return {
            'id': self.employer_id,
            'name': self.employer_name,
            'open_vacancies': self.open_vacancies_count
        }


class HHAPI:
    def __init__(self, employer_ids):
        self.employer_ids = employer_ids
        self.employers = []

    def fetch_employer_info(self, employer_id):
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

    def fetch_all_employers_info(self):
        for employer_id in self.employer_ids:
            employer = self.fetch_employer_info(employer_id)
            if employer:
                self.employers.append(employer)

    def to_json(self):
        return json.dumps([employer.to_dict() for employer in self.employers], ensure_ascii=False)

    def fetch_vacancies_by_employer_id(self, employer_id):
        employer = next((e for e in self.employers if e.employer_id == employer_id), None)
        if employer:
            response = requests.get(employer.vacancies_url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка получения вакансий для работодателя {employer_id}")
        else:
            print(f"Работодатель с ID {employer_id} не найден в списке.")


# Пример использования:
if __name__ == "__main__":
    employer_ids = [80, 89]  # Замените на реальные ID работодателей
    hh_api = HHAPI(employer_ids)
    hh_api.fetch_all_employers_info()

    for employer in hh_api.employers:
        print(f"Работодатель ID: {employer.employer_id}, Name: {employer.employer_name}, "
              f"Открыто вакансий: {employer.open_vacancies_count}, Ссылка: {employer.vacancies_url}")
