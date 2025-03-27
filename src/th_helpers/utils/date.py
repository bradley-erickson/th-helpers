from datetime import timedelta, date


def weeks_ago_3():
    today = date.today()
    weeks_ago_3 = str(today - timedelta(21))
    return weeks_ago_3
