"""Legacy IMDb request helper; catalog loading currently does not call it."""
import requests
from django.conf import settings
from requests.exceptions import RequestException


def request(url, params=None):
    try:
        headers = {
            "content-type": "application/json",
            "authorization": f"apikey {settings.IMDB_API_KEY}"
        }
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
    except RequestException:
        data = {}
    return data
