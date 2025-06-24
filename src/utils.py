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
                    print(f"ID: {employer['id']}, Name: {employer['name']}, Открыто вакансий: {employer['open_vacancies']}")
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
        found = False  # Initialize found flag
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
    vacancies = []  # Список для хранения всех вакансий
    page = 0  # Начальная страница

    while True:  # Бесконечный цикл, пока есть вакансии
        # Формируем URL для запроса вакансий
        url = f'https://api.hh.ru/vacancies?employer_id={employer_id}&page={page}'
        response = requests.get(url)

        if response.status_code == 200:  # Проверяем успешность запроса
            data = response.json()  # Преобразуем ответ в JSON
            items = data.get('items', [])  # Извлекаем вакансии

            if not items:  # Если вакансий нет, выходим из цикла
                break

            # Обрабатываем каждую вакансию
            for item in items:
                vacancy = {
                    'vacancy_id': item.get('id'),  # id вакансии
                    'name': item.get('name'),  # Название вакансии
                    'id_employer': employer_id,  # ID работодателя
                    'alternate_url': item.get('alternate_url'),
                    'salary_from': item['salary']['from'] if item['salary'] else 0,  # Минимальная зарплата
                    'salary_to': item['salary']['to'] if item['salary'] else 0  # Максимальная зарплата
                }
                vacancies.append(vacancy)  # Добавляем обработанную вакансию в список

            page += 1  # Переходим на следующую страницу
        else:
            print(f'Ошибка: {response.status_code}')  # Выводим ошибку, если произошла
            break

    return vacancies  # Возвращаем все собранные вакансии


if __name__ == '__main__':
    employer_id = '89'
    all_vacancies = get_all_vacancies(employer_id)
    get_employer_id("Домодедово")
    get_employers_with_vacancies(100)

