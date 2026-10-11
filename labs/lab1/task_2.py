users = {
    "incident_commander": {
        "role": "incident_response",
        "clearance": 4,
        "department": "CSIRT",
        "active": True,
    },
    "malware_analyst": {
        "role": "malware_researcher",
        "clearance": 3,
        "department": "Research",
        "active": True,
    },
    "monitoring_tech": {
        "role": "monitoring",
        "clearance": 2,
        "department": "NOC",
        "active": True,
    },
    "customer_rep": {
        "role": "customer_service",
        "clearance": 1,
        "department": "Customer",
        "active": True,
    },
    "backup_service": {
        "role": "service_account",
        "clearance": 2,
        "department": "System",
        "active": False,
    },
}

resources = [
    ("incident_playbook", 4),
    ("malware_lab", 3),
    ("monitoring_dashboards", 2),
    ("customer_portal", 1),
    ("emergency_procedures", 4),
    ("service_desk", 1),
    ("reverse_engineering", 3),
    ("alert_systems", 2),
    ("escalation_matrix", 3),
    ("knowledge_base", 1),
]

security_levels = (
    "Public Access",
    "Authorized",
    "Privileged",
    "Critical",
)

blocked_users = {
    "backup_service",
    "deactivated_svc",
    "policy_violation",
}

# Перетворення числового рівня безпеки на його текстову назву
def get_security_level(level):
    return security_levels[level - 1]

# Перевірка доступу користувача до ресурсу.
def check_access(username, resource):
    resource_level = resource

    # Перевірка існування користувача
    if username not in users:
        return False, "User not found"

    user = users[username]

    # Перевірка блокування
    if username in blocked_users:
        return False, "User is blocked"

    # Перевірка активності облікового запису
    if user["active"] is False:
        return False, "Account inactive"

    # Перевірка рівня допуску
    if user["clearance"] >= resource_level:
        return True, ""

    # Недостатній рівень допуску
    return False, "Insufficient clearance"


def main():

    # Виведення списку ресурсів
    print()
    print("Ресурси системи")
    print()

    for resource_name, security_level in resources:
        level_name = get_security_level(security_level)

        print(
            f"resource={resource_name:<25} "
            f"security_level={level_name}"
        )

    # Перевірка доступу
    print()
    print("Результати перевірки доступу")
    print()

    for username in users:
        for resource_name, resource_level in resources:
            allowed, reason = check_access(username, resource_level)

            if allowed:
                print(
                    f"user={username:<22} "
                    f"resource={resource_name:<25} "
                    f" -> ALLOW"
                )
            else:
                print(
                    f"user={username:<22} "
                    f"resource={resource_name:<25} "
                    f" -> DENY ({reason})"
                )

