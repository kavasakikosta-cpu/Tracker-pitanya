#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ТРЕКЕР ПИТАНИЯ
--------------
Сначала выбираете цель: прийти к обычной норме веса или к своему желаемому весу.
Затем вводите вес, рост, возраст (при своей цели — ещё и желаемый вес),
а также пол и уровень активности — они нужны для расчёта калорий.
Программа (ещё: спрашивает про аллергию и убирает опасные блюда):
  1. сравнивает ваш вес с нормой для вашего роста, возраста и пола
     (таблица для взрослых, нормы ИМТ для подростков 10–17 лет и для 65+);
  2. считает суточную калорийность, чтобы прийти к норме;
  3. делит её на приёмы пищи;
  4. предлагает блюда нужной калорийности: вес порции, ингредиенты, рецепт.

Запуск:  python tracker_pitaniya.py
"""

import math

# ----------------------------------------------------------------------------
# 1. ТАБЛИЦА НОРМ ВЕСА ПО РОСТУ (взрослые): рост, см -> (мин. кг, макс. кг)
#    Основана на нормальном ИМТ 18,5-24,9.
# ----------------------------------------------------------------------------
NORMS = {
    140: (36.3, 48.8),
    145: (38.9, 52.3),
    150: (41.6, 56.0),
    155: (44.4, 59.8),
    160: (47.4, 63.7),
    165: (50.4, 67.8),
    170: (53.5, 72.0),
    175: (56.7, 76.3),
    180: (59.9, 80.7),
    185: (63.3, 85.2),
    190: (66.8, 89.9),
    195: (70.3, 94.7),
    200: (74.0, 99.6),
}


# ----------------------------------------------------------------------------
# НОРМЫ ИМТ ДЛЯ ПОДРОСТКОВ (10–17 лет): возраст -> (5-й перцентиль, 85-й перцентиль)
# Приблизительные значения по перцентильным таблицам ИМТ для возраста (ВОЗ/CDC).
# ----------------------------------------------------------------------------
TEEN_BMI = {
    True: {  # мальчики
        10: (14.2, 19.2), 11: (14.5, 19.9), 12: (14.9, 20.7), 13: (15.4, 21.5),
        14: (16.0, 22.2), 15: (16.6, 23.0), 16: (17.2, 23.7), 17: (17.7, 24.4),
    },
    False: {  # девочки
        10: (14.0, 19.6), 11: (14.4, 20.4), 12: (14.9, 21.3), 13: (15.6, 22.1),
        14: (16.2, 22.9), 15: (16.7, 23.6), 16: (17.1, 24.2), 17: (17.4, 24.7),
    },
}

# Норма ИМТ для людей 65+ (для пожилых рекомендуют немного более высокий ИМТ)
SENIOR_BMI = (22.0, 27.0)


def age_group(age):
    if age < 18:
        return "teen"
    if age >= 65:
        return "senior"
    return "adult"


def teen_bmi_range(age, is_male):
    table = TEEN_BMI[is_male]
    a = min(max(age, 10), 17.99)
    lower = int(a)
    upper = min(lower + 1, 17)
    t = a - lower
    lo = table[lower][0] + t * (table[upper][0] - table[lower][0])
    hi = table[lower][1] + t * (table[upper][1] - table[lower][1])
    return lo, hi


def norm_range(height_cm, age=30, is_male=True):
    """
    Нормальный диапазон веса для роста и возраста.
    Возвращает (мин. кг, макс. кг, описание источника нормы).
    """
    h2 = (height_cm / 100) ** 2
    group = age_group(age)

    if group == "teen":
        bmi_lo, bmi_hi = teen_bmi_range(age, is_male)
        return (round(bmi_lo * h2, 1), round(bmi_hi * h2, 1),
                "нормы ИМТ для подростков с учётом возраста и пола")

    if group == "senior":
        return (round(SENIOR_BMI[0] * h2, 1), round(SENIOR_BMI[1] * h2, 1),
                f"норма ИМТ {SENIOR_BMI[0]:g}–{SENIOR_BMI[1]:g} для возраста 65+")

    keys = sorted(NORMS)
    if height_cm < keys[0] or height_cm > keys[-1]:
        return (round(18.5 * h2, 1), round(24.9 * h2, 1),
                "рассчитано по ИМТ 18,5–24,9 (рост вне таблицы)")
    lower = max(k for k in keys if k <= height_cm)
    upper = min(k for k in keys if k >= height_cm)
    if lower == upper:
        lo, hi = NORMS[lower]
    else:
        t = (height_cm - lower) / (upper - lower)
        lo = NORMS[lower][0] + t * (NORMS[upper][0] - NORMS[lower][0])
        hi = NORMS[lower][1] + t * (NORMS[upper][1] - NORMS[lower][1])
    return round(lo, 1), round(hi, 1), "таблица норм веса для взрослых"


# ----------------------------------------------------------------------------
# 2–3. БАЗА ПРОДУКТОВ И БЛЮД (134 блюда) — см. файл dishes_data.py
# ----------------------------------------------------------------------------
from dishes_data import KCAL100, PIECE_G, ALLERGENS, ING_ALG, DISHES


# ----------------------------------------------------------------------------
# 4. РАСЧЁТЫ
# ----------------------------------------------------------------------------
ACTIVITY = {
    "1": ("Сидячий образ жизни, мало движения", 1.2),
    "2": ("Лёгкая активность (1–3 тренировки в неделю)", 1.375),
    "3": ("Средняя активность (3–5 тренировок в неделю)", 1.55),
    "4": ("Высокая активность (6–7 тренировок в неделю)", 1.725),
}

# (название, тип блюда, доля суточной калорийности)
MEALS = [
    ("Завтрак", "breakfast", 0.25),
    ("Перекус", "snack", 0.10),
    ("Обед", "lunch", 0.30),
    ("Полдник", "snack", 0.10),
    ("Ужин", "dinner", 0.25),
]


def bmr_mifflin(weight, height, age, is_male):
    """Базовый обмен веществ по формуле Миффлина — Сан-Жеора."""
    return 10 * weight + 6.25 * height - 5 * age + (5 if is_male else -161)


def dish_kcal(dish):
    return sum(KCAL100[n] * g / 100 for n, g in dish["ingredients"])


def scale_dish(dish, target):
    """Пересчитывает рецепт под нужную калорийность порции."""
    f = target / dish_kcal(dish)
    ings = []
    for name, g in dish["ingredients"]:
        if name == "вода":
            ng = max(0, round(g * f / 10) * 10)
        else:
            ng = max(5, round(g * f / 5) * 5)
        ings.append((name, ng))
    kcal = round(sum(KCAL100[n] * g / 100 for n, g in ings))
    weight = round(dish["yield"] * f / 10) * 10
    return ings, kcal, weight, f


def dish_allergens(dish):
    return {ING_ALG[n] for n, _ in dish["ingredients"] if n in ING_ALG}


def is_blocked(dish, codes, words):
    """Блюдо нельзя, если в нём есть выбранный аллерген или слово из своего списка."""
    if dish_allergens(dish) & codes:
        return True
    text = (dish["name"] + " " + " ".join(n for n, _ in dish["ingredients"])).lower()
    return any(w in text for w in words)


def suggest(meal_type, target, codes=(), words=(), n=3, page=0):
    codes = set(codes)
    cands = [d for d in DISHES if meal_type in d["meals"] and not is_blocked(d, codes, words)]
    cands.sort(key=lambda d: abs(math.log(target / dish_kcal(d))))
    good = [d for d in cands if 0.6 <= target / dish_kcal(d) <= 1.7]
    pool = good + [d for d in cands if d not in good]   # сначала подходящие по размеру порции
    if not pool:
        return []
    start = (page * n) % len(pool)
    return [pool[(start + i) % len(pool)] for i in range(min(n, len(pool)))]


# ----------------------------------------------------------------------------
# 5. ВВОД / ВЫВОД
# ----------------------------------------------------------------------------
def ask_float(prompt, lo, hi):
    while True:
        raw = input(prompt).strip().replace(",", ".")
        try:
            value = float(raw)
        except ValueError:
            print("  Введите число.")
            continue
        if lo <= value <= hi:
            return value
        print(f"  Значение должно быть от {lo:g} до {hi:g}.")


def ask_sex():
    while True:
        raw = input("Пол (м/ж): ").strip().lower()
        if raw in ("м", "m", "муж", "мужской"):
            return True
        if raw in ("ж", "f", "жен", "женский"):
            return False
        print("  Введите «м» или «ж».")


def ask_activity():
    print("\nУровень физической активности:")
    for k, (txt, _) in ACTIVITY.items():
        print(f"  {k} — {txt}")
    while True:
        raw = input("Выберите 1–4: ").strip()
        if raw in ACTIVITY:
            return ACTIVITY[raw][1]
        print("  Введите число от 1 до 4.")


def ask_allergies():
    """Возвращает (set кодов аллергенов, список своих слов-стволов)."""
    print("\nЕсть ли у вас пищевая аллергия?")
    print("  1 — нет")
    print("  2 — да")
    while True:
        raw = input("Выберите 1 или 2: ").strip()
        if raw in ("1", "2"):
            break
        print("  Введите 1 или 2.")
    if raw == "1":
        return set(), []
    codes = list(ALLERGENS)
    print("\nНа что аллергия? Введите номера через запятую (например: 1,3).")
    for i, c in enumerate(codes, 1):
        print(f"  {i:>2} — {ALLERGENS[c]}")
    print("  Если вашего аллергена нет в списке — просто нажмите Enter и впишите его ниже.")
    chosen = set()
    while True:
        raw = input("Номера: ").strip()
        if not raw:
            break
        try:
            nums = [int(x) for x in raw.replace(" ", ",").split(",") if x]
            if all(1 <= x <= len(codes) for x in nums):
                chosen = {codes[x - 1] for x in nums}
                break
        except ValueError:
            pass
        print("  Введите номера из списка через запятую.")
    extra = input("Другие продукты, на которые аллергия (через запятую, можно пусто): ").strip().lower()
    words = []
    for w in extra.replace(";", ",").split(","):
        w = w.strip()
        if w:
            words.append(w[:-2] if len(w) > 5 else w[:-1] if len(w) > 3 else w)
    return chosen, words


def fmt_ingredient(name, grams):
    if name == "вода":
        return f"вода — {grams} мл"
    line = f"{name} — {grams} г"
    if name in PIECE_G:
        pcs = grams / PIECE_G[name]
        line += f" (≈ {pcs:.1f} шт)".replace(".0 ", " ")
    return line


def print_dish(dish, target, idx):
    ings, kcal, weight, f = scale_dish(dish, target)
    print(f"\n  {idx}) {dish['name']}")
    print(f"     Порция: ~{weight} г готового блюда, ≈ {kcal} ккал")
    if f < 0.6 or f > 1.7:
        print("     (порция заметно отличается от стандартной — при необходимости разделите"
              " на два приёма или добавьте гарнир)")
    print("     Ингредиенты:")
    for name, g in ings:
        print(f"       • {fmt_ingredient(name, g)}")
    print("     Приготовление:")
    for i, step in enumerate(dish["steps"], 1):
        print(f"       {i}. {step}")


def main():
    print("=" * 60)
    print("                 ТРЕКЕР ПИТАНИЯ")
    print("=" * 60)
    print("К какой цели вы хотите прийти?")
    print("  1 — к обычной норме веса (по таблице для моего роста и возраста)")
    print("  2 — к своему желаемому весу")
    while True:
        mode_raw = input("Выберите 1 или 2: ").strip()
        if mode_raw in ("1", "2"):
            break
        print("  Введите 1 или 2.")
    custom_goal = (mode_raw == "2")

    print("\nВведите ваши данные (дробные числа можно писать через запятую).\n")

    weight = ask_float("Вес, кг: ", 30, 250)
    height = ask_float("Рост, см: ", 120, 230)
    age = ask_float("Возраст, лет: ", 10, 110)
    desired = None
    if custom_goal:
        desired = ask_float("Желаемый вес, кг: ", 30, 250)
    is_male = ask_sex()
    activity = ask_activity()
    group = age_group(age)
    alg_codes, alg_words = ask_allergies()
    if alg_codes or alg_words:
        names = [ALLERGENS[c].split(' (')[0] for c in sorted(alg_codes)] + alg_words
        print("Учтём аллергию: " + ", ".join(names) + ". Эти блюда в рекомендации не попадут.")

    # --- сравнение с нормой (с учётом возраста и пола) ---
    lo, hi, norm_source = norm_range(height, age, is_male)
    bmi = weight / (height / 100) ** 2
    print("\n" + "-" * 60)
    print("РЕЗУЛЬТАТ СРАВНЕНИЯ С НОРМОЙ" if not custom_goal else "ВАША ЦЕЛЬ И НОРМА ВЕСА")
    print("-" * 60)
    print(f"Ваш ИМТ: {bmi:.1f}")
    print(f"Норма веса для роста {height:g} см и возраста {age:g}: {lo}–{hi} кг")
    print(f"({norm_source})")
    if custom_goal:
        desired_bmi = desired / (height / 100) ** 2
        if desired < lo:
            place = "ниже нормы"
        elif desired > hi:
            place = "выше нормы"
        else:
            place = "в пределах нормы"
        print(f"Желаемый вес {desired:g} кг — ИМТ {desired_bmi:.1f}, это {place}.")
        if desired < lo * 0.9:
            print("Желаемый вес заметно ниже нормы — такую цель лучше обсудить с врачом.")

    bmr = bmr_mifflin(weight, height, age, is_male)
    tdee = bmr * activity

    # Параметры плана зависят от возрастной группы:
    #   подростки растут — снижение/набор делаем мягче;
    #   у пожилых — умеренный дефицит, чтобы не терять мышечную массу.
    if group == "teen":
        floor = 1600 if is_male else 1400
        max_deficit, deficit_share, gain_surplus = 300, 0.10, 300
        print("Подросток растёт, поэтому план мягкий: следите за динамикой ИМТ,"
              " а не только за весом.")
    elif group == "senior":
        floor = 1400 if is_male else 1200
        max_deficit, deficit_share, gain_surplus = 300, 0.10, 300
        print("Для возраста 65+ план мягкий: важно сохранять мышцы — достаточно белка"
              " и посильная физическая активность.")
    else:
        floor = 1500 if is_male else 1200
        max_deficit, deficit_share, gain_surplus = 500, 0.20, 300

    # Границы цели: при цели «норма» — диапазон нормы,
    # при собственной цели — одна точка (желаемый вес).
    if custom_goal:
        goal_lo = goal_hi = desired
    else:
        goal_lo, goal_hi = lo, hi

    if weight > goal_hi + 0.05:
        goal = "loss"
        target_weight = goal_hi
        diff = weight - goal_hi
        if custom_goal:
            status = f"Ваша цель — снизить вес на {diff:.1f} кг (до {target_weight:g} кг)."
        else:
            status = f"Вес выше нормы на {diff:.1f} кг — цель: снижение до {target_weight} кг."
        delta = min(max_deficit, deficit_share * tdee)
        daily = max(tdee - delta, floor)
    elif weight < goal_lo - 0.05:
        goal = "gain"
        target_weight = goal_lo
        diff = goal_lo - weight
        if custom_goal:
            status = f"Ваша цель — набрать {diff:.1f} кг (до {target_weight:g} кг)."
        else:
            status = f"Вес ниже нормы на {diff:.1f} кг — цель: набор до {target_weight} кг."
        delta = gain_surplus
        daily = tdee + delta
    else:
        goal = "keep"
        target_weight = weight
        diff = 0
        if custom_goal:
            status = "Ваш вес уже равен желаемому — цель: поддержание веса."
        else:
            status = "Ваш вес в пределах нормы — цель: поддержание веса."
        delta = 0
        daily = tdee

    daily = round(daily / 10) * 10
    print(status)
    if weight < lo * 0.85:
        print("Вес заметно ниже нормы — при таком отклонении хорошо бы сверить план с врачом.")
    elif weight > hi * 1.35:
        print("Вес заметно выше нормы — при таком отклонении хорошо бы сверить план с врачом.")

    print(f"\nБазовый обмен: {bmr:.0f} ккал, с учётом активности: {tdee:.0f} ккал/сутки")
    print(f"РЕКОМЕНДУЕМАЯ КАЛОРИЙНОСТЬ: {daily:.0f} ккал в день")
    real_delta = abs(daily - tdee)
    if goal != "keep" and real_delta > 0:
        weekly = real_delta * 7 / 7700
        weeks = diff / weekly
        print(f"Темп изменения веса ≈ {weekly:.2f} кг/неделю, до цели примерно {weeks:.0f} нед.")

    # --- распределение по приёмам пищи ---
    plan = []
    print("\nПРИЁМЫ ПИЩИ")
    print("-" * 60)
    for i, (name, mtype, share) in enumerate(MEALS, 1):
        kcal = round(daily * share / 5) * 5
        plan.append((name, mtype, kcal))
        print(f"  {i}. {name:<8} — {kcal} ккал ({int(share * 100)}%)")

    # --- интерактивное меню ---
    eaten = 0
    pages = {}
    while True:
        print("\n" + "-" * 60)
        print("Выберите действие:")
        print("  1–5 — показать блюда для приёма пищи (вес порции и рецепт)")
        print("  6   — отметить съеденное (ккал)")
        print("  7   — итог дня")
        print("  0   — выход")
        choice = input("> ").strip()

        if choice == "0":
            print("Хорошего дня и приятного аппетита!")
            break
        elif choice in ("1", "2", "3", "4", "5"):
            idx = int(choice) - 1
            name, mtype, kcal = plan[idx]
            while True:
                print(f"\n=== {name.upper()} — цель {kcal} ккал ===")
                lst = suggest(mtype, kcal, alg_codes, alg_words, page=pages.get(idx, 0))
                if not lst:
                    print("  К сожалению, с вашими ограничениями подходящих блюд нет.")
                    break
                for i, dish in enumerate(lst, 1):
                    print_dish(dish, kcal, i)
                if input("\nПоказать другие варианты? (д/н): ").strip().lower() not in ("д", "y", "да"):
                    break
                pages[idx] = pages.get(idx, 0) + 1
        elif choice == "6":
            add = ask_float("Сколько ккал вы съели: ", 0, 5000)
            eaten += add
            print(f"Записано. Всего за день: {eaten:.0f} ккал.")
        elif choice == "7":
            left = daily - eaten
            print(f"\nНорма на день: {daily:.0f} ккал")
            print(f"Съедено:        {eaten:.0f} ккал")
            if left >= 0:
                print(f"Осталось:       {left:.0f} ккал")
            else:
                print(f"Превышение:     {-left:.0f} ккал")
        else:
            print("Неизвестная команда.")

    print("\nПрограмма носит справочный характер и не заменяет консультацию врача или диетолога.\nПри аллергии всегда проверяйте составы продуктов: возможны следовые количества аллергенов.")


if __name__ == "__main__":
    main()
