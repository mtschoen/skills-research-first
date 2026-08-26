"""Simple alerting used by order intake and reporting."""

ALERT_LOG = []


def send_alert(message, urgent):
    """Record and print an alert.

    ``urgent=True`` is used for time-sensitive operational issues (for
    example, low stock discovered while processing an order). ``urgent
    =False`` is used for routine informational messages (for example, a
    report finishing successfully).
    """
    prefix = "[URGENT]" if urgent else "[INFO]"
    entry = f"{prefix} {message}"
    ALERT_LOG.append(entry)
    print(entry)
    return entry


def clear_alerts():
    ALERT_LOG.clear()
