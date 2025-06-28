import requests


def get_employer_id(employer_name: str) -> None:
    """ Вспомогательная функция для определения ID работодателя по его наименованию """
    url = "https://api.hh.ru/employers"
    params = {'text': employer_name, 'area': 113}

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        found = False
        if data and 'items' in data:
            for employer in data['items']:
                if employer_name.lower() in employer['name'].lower():
                    found = True
                    print(f"ID: {employer['id']},"
                          f" Name: {employer['name']}, "
                          f"Открыто вакансий: {employer['open_vacancies']}")
            if not found:
                print("Работодатель не найден.")
        else:
            print("Работодатель не найден.")
    else:
        print("Ошибка при запросе:", response.status_code)


def get_employers_with_vacancies(min_vacancies):
    """ Вспомогательная функция для подбора работодателя по необходимому количеству вакансий """
    url = "https://api.hh.ru/employers"
    params = {'open_vacancies': min_vacancies}  # Задан фильтр по минимально необходимому количеству вакансий
    response = requests.get(url, params=params)

    if response.status_code == 200:
        employers = response.json()
        found = False
        if 'items' in employers:
            for employer in employers['items']:
                # Проверка количества вакансий на соответствие критерию
                if employer['open_vacancies'] >= min_vacancies:
                    found = True
                    print(f"Работодатель: {employer['name']}, Вакансий: {employer['open_vacancies']}")
        if not found:
            print("Не найдено работодателей с количеством вакансий", min_vacancies, "и более.")
    else:
        print("Ошибка при запросе:", response.status_code)


def get_all_vacancies(employer_id):
    """ Функция для получения всех вакансий работодателя """
    vacancies = []
    page = 0

    while True:
        url = f'https://api.hh.ru/vacancies?employer_id={employer_id}&page={page}'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])

            if not items:
                break

            for item in items:
                try:
                    vacancy = {
                        'vacancy_id': item.get('id'),
                        'name': item.get('name'),
                        'id_employer': employer_id,
                        'alternate_url': item.get('alternate_url'),
                        'salary_from': item['salary']['from'] if item['salary'] else 0,
                        'salary_to': item['salary']['to'] if item['salary'] else 0
                    }
                    vacancies.append(vacancy)
                except KeyError:
                    print(f'Ошибка с вакансией: {item.get("id")}, пропускаем.')

            page += 1
        elif response.status_code == 403:
            print(f'Ошибка 403 для работодателя {employer_id}: доступ запрещён. Пропускаем. ')  # Print the 403 error
            break
        else:
            print(f'Ошибка: {response.status_code}')
            break

    return vacancies
