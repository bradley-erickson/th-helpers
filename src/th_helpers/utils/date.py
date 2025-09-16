from datetime import timedelta, date

def days_ago(days):
    today = date.today()
    days_ago_str = str(today - timedelta(days))
    return days_ago_str


def weeks_ago_3():
    today = date.today()
    weeks_ago_3 = str(today - timedelta(21))
    return weeks_ago_3
