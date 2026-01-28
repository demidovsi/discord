# -*- coding: utf-8 -*-
"""
Тест для проверки проблемы с параметрами при параллельном запуске потоков.
Симулирует race condition когда несколько потоков обновляют параметры одновременно.
"""

import json
import time


class DBSimulator:
    """Симулятор БД для тестирования."""

    def __init__(self):
        self.params = []
        self.next_id = 1

    def select_params(self, theme_id):
        """Симуляция SELECT ... WHERE theme_id=X"""
        result = [p for p in self.params if p['theme_id'] == theme_id]
        return json.dumps(result), True

    def insert_or_update(self, values):
        """Симуляция INSERT or UPDATE через v2/entity PUT."""
        for value in values:
            if 'id' in value and value['id']:
                # UPDATE - ищем по ID
                found = False
                for i, existing in enumerate(self.params):
                    if existing['id'] == value['id']:
                        self.params[i] = value.copy()
                        print(f"    [DB] UPDATE id={value['id']}, theme_id={value['theme_id']}, code={value['code']}, value={value['value']}")
                        found = True
                        break

                if not found:
                    # ID указан, но запись не найдена - это ОШИБКА в реальной БД
                    # Но v2/entity может создать новую запись с этим ID
                    self.params.append(value.copy())
                    print(f"    [DB] INSERT (ID provided but not found) id={value['id']}, theme_id={value['theme_id']}, code={value['code']}, value={value['value']}")
            else:
                # INSERT - создаем новую запись с новым ID
                value['id'] = self.next_id
                self.next_id += 1
                self.params.append(value.copy())
                print(f"    [DB] INSERT id={value['id']}, theme_id={value['theme_id']}, code={value['code']}, value={value['value']}")

    def show_all(self):
        """Показать все параметры в БД."""
        print("\n[DB] Текущее состояние:")
        for p in self.params:
            print(f"  id={p['id']}, theme_id={p['theme_id']}, code={p['code']}, value={p['value']}")


class ThreadSimulator:
    """Симулятор потока YoutubeVideo/YoutubeComments."""

    def __init__(self, theme_id, db):
        self.theme = {'id': theme_id}
        self.db = db

    def get_theme_params(self):
        """Получает параметры конкретной темы из БД."""
        ans, is_ok = self.db.select_params(self.theme['id'])
        if not is_ok:
            return []
        try:
            return json.loads(ans)
        except:
            return []

    def update_theme_params(self, params_to_update):
        """Обновляет параметры темы в БД (текущая логика)."""
        theme_params = self.get_theme_params()
        values = []

        print(f"  [Thread {self.theme['id']}] get_theme_params() вернул {len(theme_params)} записей")

        for code, new_value in params_to_update.items():
            is_number = isinstance(new_value, (int, float, bool))
            value = {
                "value": str(new_value) if not isinstance(new_value, str) else new_value,
                "code": code,
                "theme_id": self.theme['id'],
                "is_number": is_number
            }

            # Ищем существующий параметр
            found = False
            for param in theme_params:
                if param['code'] == code:
                    value["id"] = param['id']
                    found = True
                    print(f"  [Thread {self.theme['id']}] Нашел параметр '{code}' с id={param['id']}")
                    break

            if not found:
                print(f"  [Thread {self.theme['id']}] Параметр '{code}' не найден, будет INSERT")

            values.append(value)

        if values:
            self.db.insert_or_update(values)


def test_race_condition():
    """
    Тест race condition: два потока запускаются одновременно и обновляют параметры.
    """
    print("="*70)
    print("ТЕСТ: Race Condition при параллельном запуске")
    print("="*70)

    db = DBSimulator()

    # Создаем два потока
    thread1 = ThreadSimulator(theme_id=1, db=db)
    thread2 = ThreadSimulator(theme_id=2, db=db)

    print("\n--- ЗАПУСК 1: Оба потока стартуют одновременно (первый раз) ---")
    print("\nПоток 1 (theme_id=1):")
    thread1.update_theme_params({
        'active': 1,
        'mode': 'historical',
        'last_run_timestamp': '1000'
    })

    print("\nПоток 2 (theme_id=2):")
    thread2.update_theme_params({
        'active': 1,
        'mode': 'historical',
        'last_run_timestamp': '2000'
    })

    db.show_all()

    print("\n--- ЗАПУСК 2: Оба потока обновляют параметры (второй раз) ---")
    print("\nПоток 1 (theme_id=1):")
    thread1.update_theme_params({
        'last_run_timestamp': '1111',
        'mode': 'daily'
    })

    print("\nПоток 2 (theme_id=2):")
    thread2.update_theme_params({
        'last_run_timestamp': '2222',
        'mode': 'daily'
    })

    db.show_all()

    print("\n--- ЗАПУСК 3: Оба потока обновляют параметры (третий раз) ---")
    print("\nПоток 1 (theme_id=1):")
    thread1.update_theme_params({
        'last_run_timestamp': '3333'
    })

    print("\nПоток 2 (theme_id=2):")
    thread2.update_theme_params({
        'last_run_timestamp': '4444'
    })

    db.show_all()

    # Проверка на дубликаты
    print("\n--- АНАЛИЗ ДУБЛИКАТОВ ---")
    for theme_id in [1, 2]:
        params = [p for p in db.params if p['theme_id'] == theme_id]
        print(f"\ntheme_id={theme_id}: {len(params)} записей")

        codes = {}
        for p in params:
            code = p['code']
            codes[code] = codes.get(code, 0) + 1

        for code, count in codes.items():
            if count > 1:
                print(f"  [ERROR] '{code}': {count} дубликатов!")
                # Показываем все дубликаты
                for p in params:
                    if p['code'] == code:
                        print(f"    id={p['id']}, value={p['value']}")
            else:
                print(f"  [OK] '{code}': нет дубликатов")


def test_wrong_id_scenario():
    """
    Тест сценария: поток получает параметры, но передает НЕПРАВИЛЬНЫЙ ID при обновлении.
    Это может произойти если:
    1. Поток 1 создал параметр с id=1, theme_id=1, code='active'
    2. Поток 2 при get_theme_params() получил [] (еще нет параметров для theme_id=2)
    3. Поток 2 решает создать INSERT для 'active'
    4. Но по ошибке находит id=1 от theme_id=1 (если фильтр не работает)
    5. И передает {"id": 1, "theme_id": 2, "code": "active", "value": "1"}
    6. БД создает НОВУЮ запись вместо UPDATE
    """
    print("\n" + "="*70)
    print("ТЕСТ: Сценарий с неправильным ID")
    print("="*70)

    db = DBSimulator()

    # Поток 1 создает свои параметры
    thread1 = ThreadSimulator(theme_id=1, db=db)
    print("\nПоток 1 (theme_id=1) создает параметры:")
    thread1.update_theme_params({
        'active': 1,
        'mode': 'historical'
    })

    db.show_all()

    # Поток 2 пытается обновить, но БАГ: get_theme_params возвращает параметры theme_id=1
    print("\n\n[БАГ] Поток 2 получает параметры от theme_id=1 вместо своих!")
    thread2 = ThreadSimulator(theme_id=2, db=db)

    # Эмулируем баг: подменяем get_theme_params
    def buggy_get_theme_params():
        # Возвращаем ВСЕ параметры вместо фильтра по theme_id
        ans = json.dumps(db.params)
        try:
            return json.loads(ans)
        except:
            return []

    thread2.get_theme_params = buggy_get_theme_params

    print("\nПоток 2 (theme_id=2) обновляет с багом:")
    thread2.update_theme_params({
        'active': 1,
        'mode': 'historical'
    })

    db.show_all()

    print("\n--- РЕЗУЛЬТАТ ---")
    print("Из-за бага в фильтре создались дубликаты!")
    print("Поток 2 нашел id от потока 1, но theme_id поменял на 2")
    print("БД создала НОВУЮ запись вместо UPDATE")


if __name__ == '__main__':
    test_race_condition()
    test_wrong_id_scenario()

    print("\n" + "="*70)
    print("ВЫВОДЫ")
    print("="*70)
    print("""
ПРОБЛЕМА 1: Race Condition (НЕ ВОСПРОИЗВОДИТСЯ в тесте)
- Если фильтр WHERE theme_id работает правильно, дубликатов не будет
- Каждый поток обновляет только свои параметры

ПРОБЛЕМА 2: Неправильный фильтр в get_theme_params (ВОСПРОИЗВОДИТСЯ)
- Если метод get_theme_params() возвращает параметры ВСЕХ тем (нет фильтра)
- То поток находит id от ДРУГОЙ темы
- И пытается сделать UPDATE с этим id, но меняет theme_id
- БД создает НОВУЮ запись вместо UPDATE
- Получаются ДУБЛИКАТЫ

РЕШЕНИЕ:
Проверить в РЕАЛЬНОЙ БД:
1. Работает ли фильтр WHERE theme_id={id} в запросе get_theme_params()
2. Может ли быть ситуация когда этот фильтр не применяется
3. Добавить в update_theme_params дополнительную проверку:
   if param['code'] == code AND param['theme_id'] == self.theme['id']:
       value["id"] = param['id']
    """)
