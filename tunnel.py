from pprint import pprint

from pyngrok import ngrok
from requests import get

from private_constants import URL, token, pythonanywhere_url


# URL = f'https://api.telegram.org/bot{token}/'

def launch_tunnel(pyanywhere=False):
    tunnel_url = ngrok.connect(port=5000).replace("http", "https") if not pyanywhere else pythonanywhere_url
    delete_wh_url = f'{URL}deleteWebhook'
    set_wh_url = f'{URL}setWebhook?url={tunnel_url}/{token}'
    print('Hooking:')
    pprint(get(delete_wh_url).json())
    pprint(get(set_wh_url).json())
    print(f'Hooked to: {tunnel_url}/{token}')

# TUNNEL---------------------->>>
# command line: ngrok http 5000
# TUNNEL---------------------->>>


# WEBHOOK---------------------->>>
# https://api.telegram.org/bot{token}/setWebhook?url={tunnel  or pythonanywhere url}/{token}
# https://api.telegram.org/bot{token}/deleteWebhook
# WEBHOOK---------------------->>>
