"""
mock_events.py - Simulated Day 10 Background Signals
for HackwithHyderabad 3.0 Demo.

In production, these would be populated by background
webhooks (GitHub, CI/CD, Figma, AWS CloudWatch).
"""


MOCK_DAY10_SIGNALS = {
    "emp_alice": [
        "GitHub Webhook [14:15]: Merged PR #205 "
        "('CORS & Staging API Fix') into main branch.",

        "CI/CD Pipeline [14:22]: Staging deployment "
        "build #482 completed with 0 errors."
    ],

    "emp_bob": [
        "Figma Export [11:00]: Updated mobile "
        "authentication screen assets.",

        "Local Test Runner [16:00]: Executed UI integration "
        "test suite against staging endpoint."
    ],

    "emp_charlie": [
        "AWS CloudWatch [09:30]: Automated DB backup snapshot "
        "'alpha-prod-backup-final' created successfully."
    ]
}


EMPLOYEE_NAMES = {
    "emp_alice": "Alice (Backend Lead)",
    "emp_bob": "Bob (Frontend Lead)",
    "emp_charlie": "Charlie (DevOps Lead)"
}


def get_mock_signals_for_employee(employee_id: str) -> list:
    """
    Safely retrieves Day 10 background signals for a given
    employee ID.

    Returns a default fallback list if the employee ID is
    unmapped or invalid.
    """

    if not isinstance(employee_id, str):
        return [
            "No signals available (invalid employee ID)."
        ]

    return MOCK_DAY10_SIGNALS.get(
        employee_id,
        ["No background signals recorded today."]
    )