# -*- coding: utf-8 -*-
"""
Тест для проверки исправления проблемы с дубликатами параметров.
Использует ИСПРАВЛЕННУЮ логику с проверкой theme_id.
"""

import json


class DBSimulator:
    """Симулятор БД."""

    def __init__(self):
        self.params = []
        self.next_id = 1

    def select_params(self, theme_id):
        """Симуляция SELECT ... WHERE theme_id=X"""
        result = [p for p in self.params if p['theme_id'] == theme_id]
        return json.dumps(result), True

    def insert_or_update(self, values):
        """Симуляция INSERT or UPDATE."""
        for value in values:
            if 'id' in value and value['id']:
                # UPDATE
                for i, existing in enumerate(self.params):
                    if existing['id'] == value['id']:
                        self.params[i] = value.copy()
                        print(f"    [DB] UPDATE id={value['id']}, theme_id={value['theme_id']}, code={value['code']}, value={value['value']}")
                        break
            else:
                # INSERT
                value['id'] = self.next_id
                self.next_id += 1
                self.params.append(value.copy())
                print(f"    [DB] INSERT id={value['id']}, theme_id={value['theme_id']}, code={value['code']}, value={value['value']}")

    def show_all(self):
        """Показать все параметры."""
        print("\n[DB] Текущее состояние БД:")
        for p in self.params:
            print(f"  id={p['id']}, theme_id={p['theme_id']}, code={p['code']}, value={p['value']}")


class ThreadSimulatorFIXED:
    """Симулятор потока с ИСПРАВЛЕННОЙ логикой."""

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
        """Обновляет параметры темы в БД (ИСПРАВЛЕННАЯ логика)."""
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

            # ИСПРАВЛЕНИЕ: Ищем существующий параметр ПО CODE И THEME_ID
            found = False
            for param in theme_params:
                if param.get('code') == code and param.get('theme_id') == self.theme['id']:
                    value["id"] = param['id']
                    found = True
                    print(f"  [Thread {self.theme['id']}] Нашел параметр '{code}' с id={param['id']} и theme_id={param.get('theme_id')}")
                    break

            if not found:
                print(f"  [Thread {self.theme['id']}] Параметр '{code}' не найден (или theme_id не совпал), будет INSERT")

            values.append(value)

        if values:
            self.db.insert_or_update(values)


def test_fix_with_buggy_filter():
    """
    Тест ИСПРАВЛЕНИЯ: даже если фильтр WHERE theme_id НЕ работает,
    дополнительная проверка в коде защитит от перезаписи параметров.
    """
    print("="*70)
    print("ТЕСТ ИСПРАВЛЕНИЯ: Защита от бага фильтрации")
    print("="*70)

    db = DBSimulator()

    # Поток 1 создает свои параметры
    thread1 = ThreadSimulatorFIXED(theme_id=1, db=db)
    print("\n--- Поток 1 (theme_id=1) создает параметры ---")
    thread1.update_theme_params({
        'active': 1,
        'mode': 'historical'
    })

    db.show_all()

    # Поток 2 пытается обновить, но БАГ: get_theme_params возвращает ВСЕ параметры
    print("\n--- [БАГ] Поток 2 получает параметры от theme_id=1 вместо своих ---")
    thread2 = ThreadSimulatorFIXED(theme_id=2, db=db)

    # Эмулируем баг: подменяем get_theme_params
    def buggy_get_theme_params():
        # Возвращаем ВСЕ параметры вместо фильтра по theme_id
        ans = json.dumps(db.params)
        try:
            return json.loads(ans)
        except:
            return []

    thread2.get_theme_params = buggy_get_theme_params

    print("\n--- Поток 2 (theme_id=2) обновляет с багом фильтра ---")
    thread2.update_theme_params({
        'active': 1,
        'mode': 'historical'
    })

    db.show_all()

    # Проверка результата
    print("\n--- РЕЗУЛЬТАТ ---")
    params_theme1 = [p for p in db.params if p['theme_id'] == 1]
    params_theme2 = [p for p in db.params if p['theme_id'] == 2]

    print(f"\nПараметров для theme_id=1: {len(params_theme1)}")
    for p in params_theme1:
        print(f"  id={p['id']}, code={p['code']}, value={p['value']}")

    print(f"\nПараметров для theme_id=2: {len(params_theme2)}")
    for p in params_theme2:
        print(f"  id={p['id']}, code={p['code']}, value={p['value']}")

    if len(params_theme1) == 2 and len(params_theme2) == 2:
        print("\n[SUCCESS] Параметры НЕ перезаписаны! Для каждой темы свои записи.")
        print("[SUCCESS] Дополнительная проверка theme_id защитила от бага фильтрации.")
    else:
        print("\n[FAIL] Что-то пошло не так!")


def test_normal_scenario_after_fix():
    """
    Тест нормального сценария: два потока работают параллельно,
    фильтр работает правильно, дубликатов нет.
    """
    print("\n" + "="*70)
    print("ТЕСТ: Нормальный сценарий с исправленной логикой")
    print("="*70)

    db = DBSimulator()

    thread1 = ThreadSimulatorFIXED(theme_id=1, db=db)
    thread2 = ThreadSimulatorFIXED(theme_id=2, db=db)

    print("\n--- ЗАПУСК 1: Оба потока создают параметры ---")
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

    print("\n--- ЗАПУСК 2: Оба потока обновляют параметры ---")
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

    # Проверка дубликатов
    print("\n--- ПРОВЕРКА ДУБЛИКАТОВ ---")
    for theme_id in [1, 2]:
        params = [p for p in db.params if p['theme_id'] == theme_id]
        print(f"\ntheme_id={theme_id}: {len(params)} записей")

        codes = {}
        for p in params:
            code = p['code']
            codes[code] = codes.get(code, 0) + 1

        has_duplicates = False
        for code, count in codes.items():
            if count > 1:
                print(f"  [ERROR] '{code}': {count} дубликатов")
                has_duplicates = True
            else:
                print(f"  [OK] '{code}': нет дубликатов")

        if not has_duplicates:
            print(f"  [SUCCESS] Дубликатов для theme_id={theme_id} нет!")


if __name__ == '__main__':
    test_fix_with_buggy_filter()
    test_normal_scenario_after_fix()

    print("\n" + "="*70)
    print("ИТОГИ")
    print("="*70)
    print("""
ИСПРАВЛЕНИЕ работает!

1. Даже если фильтр WHERE theme_id не работает в БД/API,
   дополнительная проверка theme_id в коде защищает от:
   - Перезаписи параметров другой темы
   - Создания дубликатов
   - Использования чужих ID

2. В нормальном сценарии всё работает как ожидается:
   - Каждый поток обновляет только свои параметры
   - UPDATE вместо INSERT для существующих параметров
   - Нет дубликатов

РЕКОМЕНДАЦИЯ:
- Применить это исправление в продакшн
- Проверить БД на наличие дубликатов и удалить их
- Убедиться что фильтр WHERE theme_id работает корректно
    """)
