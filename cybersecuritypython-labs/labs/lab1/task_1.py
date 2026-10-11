import random

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

passwords = [
    "NetworkS3c!",
    "easy",
    "Firewa11@Pass",
    "anonymous",
    "Intrus10n#Detect",
    "sample",
    "Malwar3@Scan",
    "qwerty",
    "Vulnerab1l!ty",
    "common",
]

criteria = {
    "min_length": 9,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

forbidden_passwords = {
    "easy",
    "anonymous",
    "sample",
    "qwerty",
    "common",
    "password",
}


def has_digit(password):
    return any(char.isdigit() for char in password)


def has_upper(password):
    return any(char.isupper() for char in password)


def has_special(password):
    return any(not char.isalnum() for char in password)


def check_password(password, all_passwords):
    min_length = criteria["min_length"]

    # Заборонений пароль
    if password in forbidden_passwords or len(password) < min_length:
        return "Заборонений"

    # Перевірка критеріїв
    digit_ok = has_digit(password)
    upper_ok = has_upper(password)
    special_ok = has_special(password)

    criteria_count = sum([
        digit_ok,
        upper_ok,
        special_ok,
    ])

    all_criteria = (
        digit_ok
        and upper_ok
        and special_ok
    )

    # Дуже сильний: Якщо пароль відповідає всім критеріям безпеки, має довжину
    # min_length + 4 або більше символів, та є абсолютно унікальним у всьому списку паролів

    if (
        all_criteria
        and len(password) >= min_length + 4
        and all_passwords.count(password) == 1
    ):
        return "Дуже сильний"

    # Сильний: Якщо пароль відповідає абсолютно всім критеріям безпеки, але його довжина менша
    # за min_length + 4 символів

    if all_criteria and len(password) < min_length + 4:
        return "Сильний"

    # Якщо пароль відповідає мінімальній довжині та деяким (але не всім)
    # критеріям з різних груп символів

    if criteria_count >= 2:
        return "Середній"

    # Слабкий: Якщо пароль не є забороненим і виконує хоча б один з критеріїв безпеки

    return "Слабкий"


def main():
    # Зберігаємо початкову кількість паролів
    initial_count = len(passwords)

    # Генеруємо 3 різні випадкові індекси
    random_indices = random.sample(
        range(initial_count),
        3,
    )

    # Додаємо дублікати вибраних паролів у кінець списку
    for index in random_indices:
        passwords.append(passwords[index])

    print(f"Студент: {STUDENT_NAME} {GROUP_NAME}")
    print(f"Варіант: {VARIANT_NUMBER}")
    print()

    print(f"Початкова кількість паролів: {initial_count}")
    print(f"Випадкові індекси: {random_indices}")
    print(f"Кількість паролів після додавання дублікатів: {len(passwords)}")
    print()

    # Заголовок таблиці
    print(
        f"{'№':<4}"
        f"{'Пароль':<22}"
        f"{'Довжина':<9}"
        f"{'Цифра':<8}"
        f"{'Велика':<9}"
        f"{'Спец.':<8}"
        f"{'Результат':<18}"
    )

    print()

    # Аналіз кожного пароля
    for number, password in enumerate(passwords, start=1):
        result = check_password(password, passwords)

        print(
            f"{number:<4}"
            f"{password:<22}"
            f"{len(password):<9}"
            f"{'Так' if has_digit(password) else 'Ні':<8}"
            f"{'Так' if has_upper(password) else 'Ні':<9}"
            f"{'Так' if has_special(password) else 'Ні':<8}"
            f"{result:<18}"
        )


if __name__ == "__main__":
    main()

