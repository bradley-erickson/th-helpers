from datetime import timedelta, date, datetime


def days_ago(days):
    today = date.today()
    days_ago_str = str(today - timedelta(days))
    return days_ago_str


def parse_date(raw_date_str, fallback_days=21):
    if raw_date_str:
        try:
            # Try common formats first (you can extend this list as needed)
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try:
                    return datetime.strptime(raw_date_str, fmt).date()
                except ValueError:
                    continue
            # If no format matched, raise so fallback kicks in
            raise ValueError(f"Unknown date format: {raw_date_str}")
        except Exception:
            pass  # Will fallback below

    return days_ago(fallback_days)


def weeks_ago_3():
    today = date.today()
    weeks_ago_3 = str(today - timedelta(21))
    return weeks_ago_3
