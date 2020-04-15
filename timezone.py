from datetime import datetime
from sys import _getframe

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

from data_processing import parse_time

tf = TimezoneFinder()

gl = Nominatim(user_agent='reminder_geocounter')


def get_tz_name(city):
    lc = gl.geocode(city)
    tz = tf.timezone_at(lng=float(lc.raw['lon']), lat=float(lc.raw['lat']))
    return tz


def get_user_tz_delta(data):
    try:
        parsed = parse_time(data)
        prs = datetime.today().replace(hour=int(parsed[:2]), minute=int(parsed[3:]))
        today = datetime.today()
        delta = prs - today if prs > today else today - prs
        return int(delta.total_seconds() // 3599) if prs > today else -int(delta.total_seconds() // 3599)
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False
