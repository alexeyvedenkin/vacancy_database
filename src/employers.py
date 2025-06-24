from api_service import HeadHunterAPI


class Employers():
    """ Определяет параметры для подбора работодателей с API-сервиса api.hh.ru """

    def __init__(self, data: dict) -> None:
        self.__employer_id: int = data.get('employer_id')
        self.__name: str = data.get('name')
        self.__open_vacancies: int = data.get('open_vacancies')

    def __str__(self) -> str:
        """ Возвращает формат для вывода строкового значения работодателя """
        return (f"{self.__name.strip()}, код {self.__employer_id}, количество вакансий: {self.__open_vacancies}")

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
                employer_id = data.get('employer_id')
                if employer_id not in unique_employers:
                    unique_employers[employer_id] = cls(data)
                    employers_list.append(unique_employers[employer_id])
        return employers_list


if __name__ == '__main__':
    hh_api = HeadHunterAPI('data/vacancies.json')
    query = hh_api.load_employers('УРАЛСИБ')

    # Check if any employers were found to avoid IndexError
    if query:
        print(f"Number of employers found: {len(query)}")
        print("Query data:", query[0])  # Access the first element only if the list is not empty
        employers = Employers.from_list(query)
        print("Employers:")
        for employer in employers:
            print(employer)
    else:
        print("No employers found.")