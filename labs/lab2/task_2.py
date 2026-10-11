import argparse
import csv
import json
import logging
from collections import defaultdict
from datetime import datetime, time
from pathlib import Path


CRITICAL_RESOURCES = {
    "Confidential_HR_DB",
    "Finance_Server_NAS",
    "Payroll_DB",
    "Admin_Server",
}

MASS_REQUEST_LIMIT = 50
TIME_WINDOW_SECONDS = 60


def parse_timestamp(value: str) -> datetime:
    # Перетворює timestamp з CSV у datetime.
    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue

    raise ValueError(f"Unsupported timestamp format: {value}")


def is_after_hours(timestamp: datetime) -> bool:

    if timestamp.weekday() >= 5:
        return True

    current_time = timestamp.time()
    start = time(22, 0)
    end = time(6, 0)

    return current_time >= start or current_time < end


def configure_logging(log_file: str) -> None:
    # Налаштовує логування одночасно у файл та консоль.
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def read_activity_log(path: str) -> list[dict]:
    # Читає CSV-файл активності користувачів.
    records = []

    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        required_columns = {
            "Timestamp",
            "UserID",
            "Action",
            "Resource",
            "IP",
        }

        if not required_columns.issubset(reader.fieldnames or set()):
            missing = required_columns - set(reader.fieldnames or [])
            raise ValueError(
                f"CSV is missing required columns: {', '.join(sorted(missing))}"
            )

        for row_number, row in enumerate(reader, start=2):
            try:
                timestamp = parse_timestamp(row["Timestamp"])
            except ValueError as error:
                logging.warning(
                    "Skipping row %d: %s",
                    row_number,
                    error,
                )
                continue

            records.append(
                {
                    "timestamp": timestamp,
                    "user_id": row["UserID"].strip(),
                    "action": row["Action"].strip(),
                    "resource": row["Resource"].strip(),
                    "ip": row["IP"].strip(),
                }
            )

    return records


def group_by_users(records: list[dict]) -> dict[str, list[dict]]:
    # Групує всі дії за UserID.
    grouped = defaultdict(list)

    for record in records:
        grouped[record["user_id"]].append(record)

    return grouped


def detect_off_hours(records: list[dict]) -> list[dict]:
    # Виявляє активність у позаробочий час.
    alerts = []

    for record in records:
        timestamp = record["timestamp"]

        if not is_after_hours(timestamp):
            continue

        alert = {
            "type": "off_hours",
            "user_id": record["user_id"],
            "timestamp": timestamp.isoformat(sep=" "),
            "action": record["action"],
            "resource": record["resource"],
            "ip": record["ip"],
            "reason": "Activity outside working hours or during weekend",
        }

        alerts.append(alert)

    return alerts


def detect_critical_resource_access(records: list[dict]) -> list[dict]:
    # Виявляє звернення до критичних ресурсів.
    alerts = []

    for record in records:
        if record["resource"] not in CRITICAL_RESOURCES:
            continue

        alert = {
            "type": "critical_resource",
            "user_id": record["user_id"],
            "timestamp": record["timestamp"].isoformat(sep=" "),
            "action": record["action"],
            "resource": record["resource"],
            "ip": record["ip"],
            "reason": "Access to critical resource",
        }

        alerts.append(alert)

    return alerts


def detect_mass_requests(records: list[dict]) -> list[dict]:
    # Виявляє більше 50 GET-запитів одного користувача до одного ресурсу протягом 60 секунд.

    grouped = defaultdict(list)

    for record in records:
        if record["action"].upper() == "GET":
            key = (record["user_id"], record["resource"])
            grouped[key].append(record)

    alerts = []

    for (user_id, resource), user_records in grouped.items():
        user_records.sort(key=lambda item: item["timestamp"])

        left = 0

        for right in range(len(user_records)):
            while (
                user_records[right]["timestamp"]
                - user_records[left]["timestamp"]
            ).total_seconds() > TIME_WINDOW_SECONDS:
                left += 1

            count = right - left + 1

            if count > MASS_REQUEST_LIMIT:
                first = user_records[left]
                last = user_records[right]

                alert = {
                    "type": "mass_requests",
                    "user_id": user_id,
                    "resource": resource,
                    "request_count": count,
                    "window_seconds": TIME_WINDOW_SECONDS,
                    "start_time": first["timestamp"].isoformat(sep=" "),
                    "end_time": last["timestamp"].isoformat(sep=" "),
                    "reason": (
                        f"More than {MASS_REQUEST_LIMIT} GET requests "
                        f"within {TIME_WINDOW_SECONDS} seconds"
                    ),
                }

                alerts.append(alert)

                # Не створюємо десятки однакових alert для кожного наступного запису у цьому ж вікні.
                break

    return alerts


def print_off_hours_alerts(alerts: list[dict]) -> None:
    # Виводить позаробочі події.
    print("Off-Hours Activity Alerts (22:00 - 06:00 / Weekends)")

    for alert in alerts:
        timestamp = datetime.fromisoformat(
            alert["timestamp"]
        ).strftime("%H:%M:%S")

        print(
            f"[ALERT] User '{alert['user_id']}' performed "
            f"action '{alert['action']}' at {timestamp} "
            f"(Resource: {alert['resource']})"
        )


def print_mass_request_alerts(alerts: list[dict]) -> None:
    # Виводить аномалії масових запитів.
    print("Mass Download Anomalies (>50 requests/min)")

    for alert in alerts:
        print(
            f"[ALERT] User '{alert['user_id']}' executed "
            f"{alert['request_count']} GET requests to "
            f"{alert['resource']} within 60 seconds."
        )


def save_report(
    output_path: str,
    records_count: int,
    alerts: list[dict],
) -> None:
    # Зберігає результати аналізу у JSON.
    report = {
        "summary": {
            "total_records_processed": records_count,
            "total_alerts": len(alerts),
        },
        "alerts": alerts,
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output, "w", encoding="utf-8") as file:
            json.dump(
                report,
                file,
                ensure_ascii=False,
                indent=4,
            )
    except OSError as error:
        logging.error("Failed to save report: %s", error)
        return

def create_parser() -> argparse.ArgumentParser:
    # Створює CLI parser.
    parser = argparse.ArgumentParser(
        description="User Activity Audit - anomaly detection utility"
    )

    parser.add_argument(
        "--activity-log",
        required=True,
        help="Path to CSV activity log",
    )

    parser.add_argument(
        "--after-hours",
        action="store_true",
        help="Enable detection of after-hours activity",
    )

    parser.add_argument(
        "--out-report",
        required=True,
        help="Path to JSON output report",
    )

    parser.add_argument(
        "--log-file",
        default="activity_audit.log",
        help="Path to log file",
    )

    return parser
