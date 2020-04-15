# import json
from datetime import datetime, timedelta
from re import search

from dateparser import parse

import bot_actions
import constants


# import matplotlib.pyplot as plt
# import numpy as np


def in_array(a1, a2):
    try:
        return [sub for sub in a1 if any(sub in s for s in a2)].pop()
    except IndexError:
        return None


def parse_time(text):
    if len(text) == 2 and text.isdigit():
        return f'{text}:00'
    else:
        try:
            m = search(r'\d', text)
            text = text[m.start():m.start() + 5]
            mm = search(r'[^0-9:]', text.replace(' ', ''))
            if mm is None:
                time = [x for x in text if x.isdigit()]
                time.insert(2, ':')
                try:
                    datetime.today().replace(hour=int(''.join(time[:2])), minute=int(''.join(time[3:])))
                except ValueError as e:
                    print(str(e))
                    if 'minute' in str(e):
                        return 'minute'
                    else:
                        return 'hour'
                return ''.join(time)
        except Exception:
            return None


def parse_dow(text):
    return constants.DOW[str(in_array(list(constants.DOW.keys()), [text.lower()]))]


period_options = {'at_time': parse_time,
                  'day_of_week': parse_dow}


def count_timedelta(user_dict, prev=None):
    try:
        prev = datetime.fromisoformat(user_dict['last_sending_date'])
    except KeyError:
        print('key_error in count timedelta')
    send_period = user_dict['send_period']
    time_obj = parse(parse_time(user_dict['at_time']))
    prev_date = prev if prev else datetime.today()
    if send_period in ('weekly', 'persomeweeks'):
        dow = parse_dow(user_dict['day_of_week'])
        days = (7 - (prev_date.weekday() - dow)) % (
                7 + 1 * (prev_date.weekday() == dow and (prev_date + timedelta(hours=user_dict['tz_delta'])).time()
                         > time_obj.time() and not prev))
        if prev and send_period == 'persomeweeks':
            days = days + 7 * (int(user_dict['weeks']) - 1)
        result = prev_date + timedelta(days=days)
        return result.replace(hour=time_obj.hour, minute=time_obj.minute, second=0)
    if send_period == 'daily':
        result = time_obj if time_obj - timedelta(
            hours=user_dict['tz_delta']) > datetime.today() and not prev else time_obj + timedelta(days=1)
        return result
    elif send_period in ('monthly', 'persomemonths'):
        if time_obj.day == int(user_dict['day_of_month']) and time_obj.time() > prev_date.time():
            return time_obj
        next_month = (prev_date.month + 1) % 12 if send_period == 'monthly' else (prev_date.month +
                                                                                  int(user_dict['months'])) % 12
        return prev_date.replace(year=prev_date.year + (1 * (prev_date.month + 1) >= 12),
                                 month=next_month,
                                 day=int(user_dict['day_of_month']),
                                 hour=time_obj.hour,
                                 minute=time_obj.minute,
                                 second=0)
    elif send_period == 'persomedays':
        result = prev_date + timedelta(days=int(user_dict['days']))
        return result.replace(hour=time_obj.hour, minute=time_obj.minute, second=0)


def check_correction_data(user_id, item_key, message):
    if item_key in ('days', 'weeks', 'months', 'day_of_month'):
        try:
            message = int(message)
        except ValueError:
            bot_actions.send_message(user_id, f'{message} - содержит недопустимые символы. Введите цифры, пожалуйста.')
            return False
        if message < 0:
            bot_actions.send_message(user_id,
                                     f'{message} - значение не должно быть меньше нуля. Введите корректное значение.')
            return False
    if item_key == 'day_of_week':
        if not parse_dow(message):
            bot_actions.send_message(user_id,
                                     f'{message} - некорректный ввод. Введите, пожалуйста, наименование дня недели.')
            return False
    if item_key == 'at_time':
        print(parse_time(message))
        if not parse_time(message):
            bot_actions.send_message(user_id,
                                     f'{message} - некорректный ввод. Вы можете написать,'
                                     f' к примеру "в 18 30" или просто "18".')
            return False
        elif parse_time(message) == 'minute':
            bot_actions.send_message(user_id, 'Минуты должны быть в диапазоне 0..59. Попробуйте еще раз.')
            return False
        elif parse_time(message) == 'hour':
            bot_actions.send_message(user_id, 'Часы должны быть в диапазоне 0..23. Попробуйте еще раз.')
            return False
    return True


def msg_check(text, option):
    if option is 'digit':
        return text.isdigit()
    elif option is 'alphanum':
        return text.isalphanum()
    elif option is 'alpha':
        return text.isalpha()
    elif option is 'mail_to':
        check = all([search(r'[^@]+@[^@]+\.[^@]+', mail) and mail.count('@') < 2 for mail in text.split()])
        if not check:
            return text.count('@')
        else:
            return True

# plt.style.use('dark_background')
# print(plt.style.available)
#
# fig = plt.figure()  # an empty figure with no axes
# fig.suptitle('No axes on this figure')  # Add a title so we know which it is
#
# fig, ax_lst = plt.subplots(1, 1)  # a figure with a 2x2 grid of Axes
# x = np.linspace(0, 2, 100)
# print(type(x))
# a = {'20.05': 5,
#      '20.06': 6,
#      '20.07': 4,
#      '20.08': 5,
#      '20.09': 7}
#
# plt.plot(list(a.keys()), list(a.values()), color='#DD3044', label='linear', marker='.')
#
# plt.xlabel('x label')
# plt.ylabel('y label')
#
# plt.title("Simple Plot")
#
# plt.legend()
# plt.grid(color='#525252')
# plt.show()
