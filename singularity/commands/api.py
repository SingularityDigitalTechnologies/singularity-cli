import json

from collections import namedtuple
from hashlib import sha512
from urllib.parse import urlparse
from urllib.parse import urlunparse

from requests import Request
from requests import Session

from singularity.commands.base import Command


Endpoint = namedtuple('Endpoint', ['path', 'method'])

PING_ENDPOINT = Endpoint(path='/ping', method='GET')

BATCH_INFO_ENDPOINT = Endpoint(path='/batch', method='GET')
BATCH_ADD_ENDPOINT = Endpoint(path='/batch', method='POST')


class AbstractRequest(Command):
    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        api_url = options.get('--api-url')
        url_params = urlparse(api_url)
        if not url_params[0]:
            raise SystemExit('--api-url requires a scheme e.g. http')

        self.scheme = url_params[0]
        self.netloc = url_params[1]

        self.secret = options.get('secret', '')
        self.api_key = options.get('api-key', '')

    def generate_sha512_hmac(self, secret, method, endpoint, payload):
        base_sig = '%s\n%s\n%s' % (method, endpoint, payload)
        return hmac.new(
            secret.encode('utf-8'), bytes(base_sig).encode('utf-8'),
            digestmod=hashlib.sha512
        ).hexdigest()

    def get_headers(self, endpoint, payload):
        if not self.secret:
            print('WARNING: API key and/or secret not set')
            return {}

        signature = self.generate_sha512_hmac(
            self.secret,
            endpoint.method,
            endpoint.path,
            payload
        )

        return {
            'X-singularity-apikey': self.key,
            'X-singularity-signature': signature,
        }

    def send_request(self, endpoint, payload='', headers=None):
        url = urlunparse((
            self.scheme,
            self.netloc,
            endpoint.path,
            '',
            '',
            ''
        ))

        headers = headers or {}
        request = Request(endpoint.method, url, data=payload, headers=headers)

        return Session().send(request.prepare())

    def request(self, endpoint, payload=''):
        headers = self.get_headers(endpoint, payload)
        response = self.send_request(endpoint, payload=payload, headers=headers)

        trace = response.headers.get('X-atlas-trace')

        payload = None
        try:
            payload = response.json()
        except ValueError:
            pass

        print(
            '[%s][%d][%s] %s' % (
                endpoint.path,
                response.status_code,
                trace,
                payload or response.text
            )
        )


class Ping(AbstractRequest):

    def run(self):
        self.request(PING_ENDPOINT)


class BatchAdd(AbstractRequest):

    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        self.payload = options.get('<payload>', '')
        self.type = options.get('--type', '')
        self.priority = options.get('--priority', 0)

    def run(self):

        payload = json.dumps({
	    'type': self.type,
	    'priority': self.priority,
	    'job_data': self.payload,
        })

        self.request(BATCH_ADD_ENDPOINT, payload)


class BatchStatus(AbstractRequest):

    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        self.endpoint = BATCH_INFO_ENDPOINT

        uuid = options.get('--uuid')
        if uuid:
            self.endpoint = Endpoint(path='/batch/%s' % uuid, method='GET')

    def run(self):
        self.request(self.endpoint)
