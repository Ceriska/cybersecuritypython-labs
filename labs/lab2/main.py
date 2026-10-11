import logging
from datetime import datetime, timedelta, timezone

def main() -> None:
    print("Лабораторна робота №2")

    print("\nЗавдання 1")
    from task_1 import (
        User,
        Admin,
        UserAccount,
        SESSION_TIMEOUT_SEC,
    )
    # Створення користувача
    user = User(
            username="student",
            email="student_01@example.com",
            role="user",
        )

    user.set_password("SecretPassword123")

    print("\n1. Користувач:")
    print(user)

    # Перевірка пароля-
    print("\n2. Перевірка пароля:")

    print(
            "Правильний пароль:",
            user.check_password("SecretPassword123"),
        )

    print(
            "Неправильний пароль:",
            user.check_password("WrongPassword"),
        )

    # Email
    print("\n3. Зміна email:")

    user.email = "new_student@example.com"
    print("Новий email:", user.email)

    try:
        user.email = "invalid-email"
    except ValueError as error:
        print("Помилка валідації:", error)

        # Адміністратор
    print("\n4. Адміністратор:")

    admin = Admin(
        username="admin",
        email="admin@example.com",
        permissions={"read"},
        )

    admin.set_password("AdminPassword123")

    admin.grant_permission("write")
    admin.grant_permission("delete")

    print(admin)

    print(
        "Має permission 'write':",
        admin.has_permission("write"),
        )

    admin.revoke_permission("delete")

    print("Після revoke:", admin)

        # UserAccount та AuditLog
    print("\n5. UserAccount:")

    account = UserAccount(user)

    print("Невдалий вхід:")
    result = account.login(
        username="student",
        password="WrongPassword",
        ip="192.168.1.10",
        )
    print("Результат:", result)

    print("\nУспішний вхід:")
    result = account.login(
        username="student",
        password="SecretPassword123",
        ip="192.168.1.10",
        )
    print("Результат:", result)
    print("Авторизований:", account.is_authenticated())

    # __getitem__ / __setitem__
    print("\n6. Доступ через []:")

    print("account['user']:", account["user"])
    print("account['session']:", account["session"])

    # Демонстрація таймауту
    print("\n7. Таймаут сеансу:")

    if account.session is not None:
        account.session.last_activity = (
                datetime.now(timezone.utc)
                    - timedelta(seconds=SESSION_TIMEOUT_SEC + 1)
            )

        print(
            "Авторизований після таймауту:",
            account.is_authenticated(),
        )

        # Вихід
        print("\n8. Вихід із системи:")

        account.logout()

        print("Сеанс:", account.session)
        print("Авторизований:", account.is_authenticated())

        print("\n9. AuditLog:")

        account.audit_log.show_all()

    print("\nЗавдання 2")
    from task_2 import (
        configure_logging,
        read_activity_log,
        group_by_users,
        detect_off_hours,
        detect_critical_resource_access,
        detect_mass_requests,
        save_report,
        create_parser
    )

    configure_logging("data/activity_audit.log")
    activity_log = "data/activity.csv"
    output_report = "report.json"

    try:
        records = read_activity_log(activity_log)
    except (OSError, ValueError) as error:
        print(f"Помилка читання файлу: {error}")
        return

    logging.info("Total records processed: %d.", len(records))
    users = group_by_users(records)
    logging.info("Unique users found: %d.", len(users))

    # Аналіз позаробочого часу
    off_hours_alerts = detect_off_hours(records)

    print("\nOff-Hours Activity Alerts")

    for alert in off_hours_alerts:
        print(
            f"[ALERT] User '{alert['user_id']}' "
            f"performed '{alert['action']}' "
            f"at {alert['timestamp']} "
            f"(Resource: {alert['resource']})"
        )

    # Аналіз критичних ресурсів
    critical_alerts = detect_critical_resource_access(records)

    print("\nCritical Resource Alerts")

    for alert in critical_alerts:
        print(
            f"[ALERT] User '{alert['user_id']}' "
            f"accessed critical resource "
            f"'{alert['resource']}' "
            f"at {alert['timestamp']}"
            )

        # Аналіз масових запитів
        mass_alerts = detect_mass_requests(records)

        print("\nMass Request Alerts")

        for alert in mass_alerts:
            print(
                f"[ALERT] User '{alert['user_id']}' "
                f"executed {alert['request_count']} GET requests "
                f"to '{alert['resource']}' "
                f"within {alert['window_seconds']} seconds."
            )

        # Об'єднуємо всі alerts
        all_alerts = (
                off_hours_alerts
                + critical_alerts
                + mass_alerts
        )

        parser = create_parser()
        args = parser.parse_args()

        configure_logging(args.log_file)

        logging.info("Reading user activity log %s...", args.activity_log)

        try:
            records = read_activity_log(args.activity_log)
        except (OSError, ValueError) as error:
            logging.error("Failed to read activity log: %s", error)
            return

        logging.info("Total records processed: %d.", len(records))

        # defaultdict використовується відповідно до умови завдання.
        users = group_by_users(records)
        logging.info("Unique users found: %d.", len(users))

        all_alerts = []

        if args.after_hours:
            off_hours_alerts = detect_off_hours(records)
            all_alerts.extend(off_hours_alerts)

        critical_alerts = detect_critical_resource_access(records)
        all_alerts.extend(critical_alerts)

        mass_alerts = detect_mass_requests(records)
        all_alerts.extend(mass_alerts)

        save_report(
            args.out_report,
            len(records),
            all_alerts,
        )

        logging.info(
            "Anomalous activity report written to %s",
            args.out_report,
        )

        # Зберігаємо результат
        try:
            save_report(
                output_report,
                len(records),
                all_alerts,
            )
        except OSError as error:
            print(f"Помилка збереження звіту: {error}")
            return

        print(
            f"\nЗвіт збережено у файл: {output_report}"
        )

if __name__ == "__main__":
    main()
