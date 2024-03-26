import datetime


def next_five_years():
    today = datetime.date.today()
    year = today.year
    period = 3
    years = [year - 1 + i for i in range(period)]

    return years
