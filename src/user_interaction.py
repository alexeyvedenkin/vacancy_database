import json

from config import EMPLOYERS_ID
from src.db_maker import DBMaker
from src.db_manager import DBManager
from src.hh_api import HHAPI
from src.utils import get_all_vacancies, load_fixtures


def user_interaction() -> None:
    """ Определяет процедуру взаимодействия с пользователем """
    print()
    print('Вас приветствует программа работы с базой данных, содержащей вакансии с сайта api.hh.ru')
    print()

    db_name = input(
        'Введите название базы данных\n'
        'ВНИМАНИЕ! При совпадении наименований существующая база '
        'данных будет удалена\n'
    ).strip()

    db_maker = DBMaker()
    db_maker.db_name = db_name

    # Проверка существования базы данных с введенным названием
    if db_maker.database_exists(db_name):
        confirm = input(f"База данных '{db_name}' уже существует. Удалить ее? (да/нет): ")
        if confirm.lower() != 'да':
            print("Создание базы данных отменено. Пожалуйста, введите новое название.")
            return user_interaction()

        print(f"Удаление существующей базы данных '{db_name}'...")
        db_maker.delete_database(db_name)

    # Создание новой базы данных
    db_maker.create_database(db_name)
    print(f"База данных '{db_name}' успешно создана")

    print()

    # Выбор способа заполнения базы данных
    choice = input("Выберите способ заполнения базы данных:\n"
                   "1. API (api.hh.ru)\n"
                   "2. Фикстуры (загрузка из JSON)\n"
                   "Введите 1 или 2: ")
    if choice == '1':
        hh_api = HHAPI(EMPLOYERS_ID)
        hh_api.fetch_all_employers_info()
        employers_json = hh_api.to_json()
        db_maker.create_table('employers', employers_json)
        db_maker.fill_table('employers', employers_json)
        print("Сформирована таблица 'employers' с данными о работодателях")
        print(f"В таблицу загружены данные о {len(EMPLOYERS_ID)} работодателях")
        print()
        print(f'Ожидайте, выполняется подбор вакансий и загрузка их в базу данных "{db_name}"')

        all_vacancies = []

        for employer in EMPLOYERS_ID:
            try:
                vacancies = get_all_vacancies(employer)
                print(f'Количество вакансий у работодателя c ID={employer}: {len(vacancies)}')
                all_vacancies.extend(vacancies)
                print(f'Текущее количество отобранных вакансий: {len(all_vacancies)}')
            except Exception as e:
                print(f"Error for employer {employer}: {e}")

        # Convert vacancies to JSON and handle errors
        try:
            vacancies_json = json.dumps(all_vacancies, ensure_ascii=False)
            db_maker.create_table('vacancies', vacancies_json)
            db_maker.fill_table('vacancies', vacancies_json)
            print("Сформирована таблица 'vacancies' с данными о вакансиях")
            print(f"В таблицу загружены данные о {len(all_vacancies)} вакансиях")
            print()
        except Exception as e:
            print(f'Ошибка при работе с вакансиями: {e}')

    elif choice == '2':
        load_fixtures(db_maker)  # Вызываем функцию загрузки фикстур
        print()

    else:
        print("Неверный выбор, пожалуйста, перезапустите программу.")

    db_manager = DBManager(db_name)

    print(f'База данных {db_name} сформирована. \n'
          f'Доступные режимы работы с базой: \n'
          f'Полный - вывод всех вакансий и сохранение результата в CSV-файл \n'
          f'Облегченный - количество выводимых вакансий определяется пользователем,'
          f'информация о всех вакансиях сохраняется в CSV-файл')

    print()

    try:
        mode_input = input("Выберите режим отображения (1 - Полный, любой другой символ - Облегченный): ").strip()

        if mode_input == '1':
            mode = 'полный'
        else:
            mode = 'облегченный'

        if mode == 'облегченный':
            count_input = input("Введите количество вакансий для вывода: ")
            if not count_input:
                print('По умолчанию установлен вывод 5 вакансий')
                count = 5
            else:
                try:
                    count = int(count_input)
                except ValueError:
                    print('Ошибка: Введите целое число. По умолчанию установлен вывод 5 вакансий')
                    count = 5
        else:
            count = None

        print()

        print(f"Выбранный режим: {mode}")
        if count is not None:
            print(f"Количество вакансий для вывода: {count}")

        print()

        print("Сведения о работодателях и количестве открытых вакансий:")
        info_from_company_and_vacancies = db_manager.get_companies_and_vacancies_count()
        print(f"{'ID':<10} {'Company Name':<60} {'Open Vacancies':<10}")
        print("-" * 80)

        for employer in info_from_company_and_vacancies:
            employer_id = getattr(employer, 'employer_id', 'N/A')
            employer_name = getattr(employer, 'name', 'Unknown Company')
            vacancies_count = getattr(employer, 'open_vacancies', 0)
            print(f"{employer_id:<10} {employer_name:<60} {vacancies_count:<10}")

        print()

        input("Нажмите Enter, чтобы перейти к сведениям об открытых вакансиях...")

        print("Сведения об открытых вакансиях")
        vacancies = db_manager.get_all_vacancies()

        for vacancy in vacancies[:count] if count is not None else vacancies:
            print(vacancy)

        print()
        print(f'Выведены сведения о {len(vacancies[:count])} вакансий из имеющихся {len(vacancies)}')
        print('Полный список вакансий выгружен в файл "data/all_vacancies.csv"')
        print()

        input("Нажмите Enter, чтобы перейти к средней зарплате...")

        avg_salary = db_manager.get_avg_salary()
        print(f'Средняя зарплата по отобранным вакансиям: {round(avg_salary, 2)}')
        print()

        input("Нажмите Enter, чтобы перейти к вакансиям с зарплатой выше средней...")
        print("Сведения о вакансиях с зарплатой выше средней")
        higher_vacancies = db_manager.get_vacancies_with_higher_salary()
        for vacancy in higher_vacancies[:count] if count is not None else higher_vacancies:
            print(vacancy)

        print()
        print(f'Выведены сведения о {len(higher_vacancies[:count])} вакансий из имеющихся {len(higher_vacancies)}')
        print('Полный список вакансий выгружен в файл "data/higher_salary_vacancies.csv"')
        print()

        input("Нажмите Enter, чтобы перейти к фильтрации вакансий...")

        while True:
            user_key = input('Введите ключевое слово для фильтрации вакансий (нажмите Enter, чтобы завершить): ')

            if user_key == "":
                print("Выход из фильтрации.")
                break

            print()
            filtered_vacancies = db_manager.get_vacancies_with_keyword(user_key)

            for vacancy in filtered_vacancies[:count] if count is not None else filtered_vacancies:
                print(vacancy)

            print(
                f'Выведены сведения о {len(filtered_vacancies[:count])} '
                f'вакансий из имеющихся {len(filtered_vacancies)}')
            print(f'Полный список вакансий выгружен в файл "data/vacancies_with_{user_key}.csv"')

    except Exception as e:
        print(f'Ошибка при извлечении данных: {e}')

    db_manager.close()


if __name__ == '__main__':
    user_interaction()
