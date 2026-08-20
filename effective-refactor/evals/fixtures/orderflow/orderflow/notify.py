"""Simple alerting used by order intake and reporting."""

ALERT_LOG = []


def _record_alert(prefix, message):
    entry = f"{prefix} {message}"
    ALERT_LOG.append(entry)
    print(entry)
    return entry


def send_page(message):
    """Send a time-sensitive operational page (for example, low stock)."""
    return _record_alert("[URGENT]", message)


def send_routine_notice(message):
    """Send a routine informational notice (for example, a completed report)."""
    return _record_alert("[INFO]", message)


def clear_alerts():
    ALERT_LOG.clear()
