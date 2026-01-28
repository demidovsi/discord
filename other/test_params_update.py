# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки логики обновления параметров темы
без обращения к YouTube API.
"""

import json


class MockParamsTest:
    """Имитация логики update_theme_params для тестирования."""

    def __init__(self, theme_id):
        self.theme_id = theme_id
        self.db_params = []  # Имитация БД

    def get_theme_params(self):
        """Имитация загрузки параметров из БД."""
        return [p for p in self.db_params if p.get('theme_id') == self.theme_id]

    def save_to_db(self, params):
        """Имитация сохранения в БД."""
        for param in params:
            # Ищем существующий параметр по ID
            found = False
            for i, existing in enumerate(self.db_params):
                if existing.get('id') == param.get('id'):
                    # UPDATE
                    self.db_params[i] = param.copy()
                    print(f"  UPDATE: id={param['id']}, code={param['code']}, value={param['value']}, theme_id={param['theme_id']}")
                    found = True
                    break

            if not found:
                # INSERT - генерируем новый ID
                new_id = len(self.db_params) + 1
                param['id'] = new_id
                self.db_params.append(param.copy())
                print(f"  INSERT: id={new_id}, code={param['code']}, value={param['value']}, theme_id={param['theme_id']}")

    def update_theme_params_OLD(self, params_to_update):
        """СТАРАЯ логика (с ошибкой) - для сравнения."""
        theme_params = self.get_theme_params()
        values = []

        for code, new_value in params_to_update.items():
            is_number = isinstance(new_value, (int, float, bool))
            value = {
                "value": str(new_value) if not isinstance(new_value, str) else new_value,
                "code": code,
                "theme_id": self.theme_id,
                "is_number": is_number
            }

            # Ищем существующий параметр
            for param in theme_params:
                if param.get('code') == code:
                    value["id"] = param['id']
                    break

            values.append(value)

        if values:
            self.save_to_db(values)

    def update_theme_params_NEW(self, params_to_update):
        """НОВАЯ логика (исправленная) - для сравнения."""
        theme_params = self.get_theme_params()
        values = []

        for code, new_value in params_to_update.items():
            is_number = isinstance(new_value, (int, float, bool))
            value = {
                "value": str(new_value) if not isinstance(new_value, str) else new_value,
                "code": code,
                "theme_id": self.theme_id,
                "is_number": is_number
            }

            # Ищем существующий параметр ПО CODE И THEME_ID
            found = False
            for param in theme_params:
                if param.get('code') == code and param.get('theme_id') == self.theme_id:
                    value["id"] = param['id']
                    found = True
                    break

            values.append(value)

        if values:
            self.save_to_db(values)


def test_scenario_1_old():
    """Тест 1: СТАРАЯ логика - два потока обновляют параметры."""
    print("\n" + "="*70)
    print("ТЕСТ 1: СТАРАЯ ЛОГИКА (с ошибкой)")
    print("="*70)

    # Создаем два потока для разных тем
    theme1 = MockParamsTest(theme_id=1)
    theme2 = MockParamsTest(theme_id=2)

    # Используем общую "БД" для обоих
    shared_db = []
    theme1.db_params = shared_db
    theme2.db_params = shared_db

    print("\n--- Поток 1 (theme_id=1): первый запуск ---")
    theme1.update_theme_params_OLD({
        'active': 1,
        'last_run_timestamp': '1704056400.123',
        'date': '2024-01-01 00:00:00'
    })

    print("\n--- Поток 2 (theme_id=2): первый запуск ---")
    theme2.update_theme_params_OLD({
        'active': 1,
        'last_run_timestamp': '1704056500.456',
        'date': '2024-01-01 00:10:00'
    })

    print("\n--- Поток 1 (theme_id=1): второй запуск ---")
    theme1.update_theme_params_OLD({
        'last_run_timestamp': '1704056600.789',
        'date': '2024-01-01 00:20:00'
    })

    print("\n--- Поток 2 (theme_id=2): второй запуск ---")
    theme2.update_theme_params_OLD({
        'last_run_timestamp': '1704056700.111',
        'date': '2024-01-01 00:30:00'
    })

    print("\n--- ИТОГОВОЕ СОСТОЯНИЕ БД ---")
    for param in shared_db:
        print(f"  id={param['id']}, theme_id={param['theme_id']}, code={param['code']}, value={param['value']}")

    # Анализ проблемы
    print("\n--- АНАЛИЗ ПРОБЛЕМЫ ---")
    theme1_params = [p for p in shared_db if p['theme_id'] == 1]
    theme2_params = [p for p in shared_db if p['theme_id'] == 2]

    print(f"Параметров для theme_id=1: {len(theme1_params)}")
    print(f"Параметров для theme_id=2: {len(theme2_params)}")

    # Проверяем дубликаты
    codes_theme1 = {}
    for p in theme1_params:
        code = p['code']
        codes_theme1[code] = codes_theme1.get(code, 0) + 1

    codes_theme2 = {}
    for p in theme2_params:
        code = p['code']
        codes_theme2[code] = codes_theme2.get(code, 0) + 1

    print(f"\nДубликаты для theme_id=1:")
    for code, count in codes_theme1.items():
        if count > 1:
            print(f"  [ERROR] '{code}': {count} записей")
        else:
            print(f"  [OK] '{code}': {count} запись")

    print(f"\nДубликаты для theme_id=2:")
    for code, count in codes_theme2.items():
        if count > 1:
            print(f"  [ERROR] '{code}': {count} записей")
        else:
            print(f"  [OK] '{code}': {count} запись")


def test_scenario_2_new():
    """Тест 2: НОВАЯ логика - два потока обновляют параметры."""
    print("\n" + "="*70)
    print("ТЕСТ 2: НОВАЯ ЛОГИКА (исправленная)")
    print("="*70)

    # Создаем два потока для разных тем
    theme1 = MockParamsTest(theme_id=1)
    theme2 = MockParamsTest(theme_id=2)

    # Используем общую "БД" для обоих
    shared_db = []
    theme1.db_params = shared_db
    theme2.db_params = shared_db

    print("\n--- Поток 1 (theme_id=1): первый запуск ---")
    theme1.update_theme_params_NEW({
        'active': 1,
        'last_run_timestamp': '1704056400.123',
        'date': '2024-01-01 00:00:00'
    })

    print("\n--- Поток 2 (theme_id=2): первый запуск ---")
    theme2.update_theme_params_NEW({
        'active': 1,
        'last_run_timestamp': '1704056500.456',
        'date': '2024-01-01 00:10:00'
    })

    print("\n--- Поток 1 (theme_id=1): второй запуск ---")
    theme1.update_theme_params_NEW({
        'last_run_timestamp': '1704056600.789',
        'date': '2024-01-01 00:20:00'
    })

    print("\n--- Поток 2 (theme_id=2): второй запуск ---")
    theme2.update_theme_params_NEW({
        'last_run_timestamp': '1704056700.111',
        'date': '2024-01-01 00:30:00'
    })

    print("\n--- ИТОГОВОЕ СОСТОЯНИЕ БД ---")
    for param in shared_db:
        print(f"  id={param['id']}, theme_id={param['theme_id']}, code={param['code']}, value={param['value']}")

    # Анализ
    print("\n--- АНАЛИЗ ---")
    theme1_params = [p for p in shared_db if p['theme_id'] == 1]
    theme2_params = [p for p in shared_db if p['theme_id'] == 2]

    print(f"Параметров для theme_id=1: {len(theme1_params)}")
    print(f"Параметров для theme_id=2: {len(theme2_params)}")

    # Проверяем дубликаты
    codes_theme1 = {}
    for p in theme1_params:
        code = p['code']
        codes_theme1[code] = codes_theme1.get(code, 0) + 1

    codes_theme2 = {}
    for p in theme2_params:
        code = p['code']
        codes_theme2[code] = codes_theme2.get(code, 0) + 1

    print(f"\nДубликаты для theme_id=1:")
    for code, count in codes_theme1.items():
        if count > 1:
            print(f"  [ERROR] '{code}': {count} записей")
        else:
            print(f"  [OK] '{code}': {count} запись")

    print(f"\nДубликаты для theme_id=2:")
    for code, count in codes_theme2.items():
        if count > 1:
            print(f"  [ERROR] '{code}': {count} записей")
        else:
            print(f"  [OK] '{code}': {count} запись")


if __name__ == '__main__':
    # Запускаем оба теста
    test_scenario_1_old()
    test_scenario_2_new()

    print("\n" + "="*70)
    print("ВЫВОДЫ")
    print("="*70)
    print("""
ПРОБЛЕМА в старой логике:
- При поиске существующего параметра метод проверяет только CODE
- Но НЕ проверяет THEME_ID
- В результате поток theme_id=2 находит параметр от theme_id=1 (у них одинаковый code)
- И использует его ID для "обновления"
- Но theme_id в новой записи = 2, поэтому создается НОВАЯ запись
- А старая запись остается в БД

РЕШЕНИЕ:
- При поиске существующего параметра проверять И code И theme_id
- Тогда каждый поток будет находить только СВОИ параметры
- И правильно их обновлять вместо создания дубликатов
    """)
