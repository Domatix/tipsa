import requests
import json


class TipsaAPI:
    def __init__(self, url_base=False, token=False):
        self.url_base = url_base or 'http://asmensga.tlsi.es:8088/'
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'charset': 'utf-8',
            'Authorization': f'Bearer {token}',
        }

    def send_request(self, endpoint, data):
        url = f"{self.url_base}/{endpoint}"
        return requests.post(url, headers=self.headers, data=json.dumps(data))

    def get_request(self, endpoint):
        url = f"{self.url_base}/{endpoint}"
        return requests.get(url, headers=self.headers)
