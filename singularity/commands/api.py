from collections import namedtuple
from urllib.parse import urlparse
from urllib.parse import urlunparse

from requests import Request
from requests import Session

from singularity.commands.base import Command


Endpoint = namedtuple('Endpoint', ['path', 'method'])

PING_ENDPOINT = Endpoint(path='/ping', method='GET')

BATCH_INFO_ENDPOINT = Endpoint(path='/batch', method='GET')
BATCH_ADD_ENDPOINT = Endpoint(path='/batch', method='POST')


class Ping(Command):

    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        api_url = options.get('--api-url')
        url_params = urlparse(api_url)
        if not url_params[0]:
            raise SystemExit('--api-url requires a scheme e.g. http')

        self.scheme = url_params[0]
        self.netloc = url_params[1]

    def send_request(self, endpoint, data=None, headers=None):
        url = urlunparse((
            self.scheme,
            self.netloc,
            endpoint.path,
            '',
            '',
            ''
        ))

        data = data or {}
        headers = headers or {}

        request = Request(endpoint.method, url, data=data, headers=headers)

        return Session().send(request.prepare())

    def run(self):
        response = self.send_request(PING_ENDPOINT)

        payload = None
        try:
            payload = response.json()
        except ValueError:
            pass

        print('[%s] %s' % (response.status_code, payload or response.text))


class BatchAdd(Command):
    def run(self):
        pass
