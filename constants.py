from enum import Enum


class States(Enum):
    S_START = "0"
    S_ENTER_DATA = "1"
    S_USER_WAIT = "4"
    S_SET_TEMPLATE = "5"
    S_SET_MAILTHEME = "6"
    S_SET_MAIL_TO = "7"
    S_SET_DATE = "8"
    S_CORRECT_DATE = "9"
    S_SET_TIMER = "10"
    S_DOING_NOTHING = "11"
    S_SET_TIMEZONE = "12"


corQuests = [
    {'days': [' - сколько дней?', 'Дней: ']},
    {'weeks': [' - сколько недель?', 'Недель: ']},
    {'months': [' - сколько месяцев?', 'Месяцев: ']},
    {'day_of_week': [' - в какой день недели?', 'День недели: ']},
    {'day_of_month': [' - какого числа?', 'День месяца: ']},
    {'at_time': [' - во сколько?', 'Время отправки: ']},
]

choose_period = {
    'daily': ("Ежедневно", 'at_time'),
    'weekly': ("Еженедельно", 'day_of_week', 'at_time'),
    'monthly': ("Ежемесячно", 'day_of_month', 'at_time'),
    'persomedays': ("Раз в несколько дней", 'days', 'at_time'),
    'persomeweeks': ("Раз в несколько недель", 'weeks', 'day_of_week', 'at_time'),
    'persomemonths': ("Раз в несколько месяцев", 'months', 'day_of_month', 'at_time'),
}

DOW = {
    'понедельник': 0,
    'вторник': 1,
    'сред': 2,
    'четверг': 3,
    'пятниц': 4,
    'суббот': 5,
    'воскресень': 6,
    'None': None,
}

EVERY = {
    'день': 'day',
    'ежедневно': 'day',
    'неделю': 'week',
    'еженедельно': 'week',
    'месяц': 'month',
    'ежемесячно': 'month',
}
