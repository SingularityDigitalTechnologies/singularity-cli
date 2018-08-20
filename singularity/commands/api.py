import hmac
import json
import pprint
import requests

from collections import namedtuple
from hashlib import sha512
from urllib.parse import urlparse
from urllib.parse import urlunparse

from requests import Request
from requests import Session

from singularity.commands.base import Command


Endpoint = namedtuple('Endpoint', ['path', 'method'])

PING_ENDPOINT = Endpoint(path='/ping', method='GET')

ATLAS_STATUS_ENDPOINT = Endpoint(path='/status', method='GET')
BATCH_INFO_ENDPOINT = Endpoint(path='/batch', method='GET')
BATCH_ADD_ENDPOINT = Endpoint(path='/batch', method='POST')
JOB_INFO_ENDPOINT = Endpoint(path='/job', method='GET')


class AbstractRequest(Command):
    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        api_url = options.get('--api-url')
        url_params = urlparse(api_url)
        if not url_params[0]:
            raise SystemExit('--api-url requires a scheme e.g. http')

        self.scheme = url_params[0]
        self.netloc = url_params[1]

        self.secret = options.get('--secret', '')
        self.api_key = options.get('--api-key', '')

    def generate_sha512_hmac(self, secret, method, endpoint, payload):
        base_sig = '%s\n%s\n%s' % (method, endpoint, payload)
        return hmac.new(
            secret.encode('utf-8'),
            bytes(base_sig.encode('utf-8')),
            digestmod=sha512
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
            'X-singularity-apikey': self.api_key,
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

        try:
            response = Session().send(request.prepare())
        except requests.exceptions.ConnectionError:
            raise SystemExit('Unable to establish connection with API')
        else:
            return response

    def request(self, endpoint, payload=''):
        headers = self.get_headers(endpoint, payload)
        response = self.send_request(
            endpoint,
            payload=payload,
            headers=headers,
        )

        trace = response.headers.get('X-atlas-trace', '')

        payload = None
        try:
            payload = response.json()
        except ValueError:
            pass

        print('[%s][%d][%s]\n' % (endpoint.path, response.status_code, trace))
        pprint.PrettyPrinter(indent=4).pprint(payload or response.text)


class Ping(AbstractRequest):

    def run(self):
        self.request(PING_ENDPOINT)


class BatchAdd(AbstractRequest):

    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        payload = options.get('<payload>', '[]')
        try:
            self.payload = json.loads(payload)
        except ValueError:
            raise SystemExit('Payload not JSON decodable')

        self.type = options.get('--type', '')
        priority = options.get('--priority', '0')

        if not priority.isdigit():
            raise SystemExit('Priority must be an integer number')

        self.priority = int(priority)
        cpus = options.get('--cpus', '0')
        if not cpus.isdigit():
            raise SystemExit('Priority must be an integer number')

        self.cpus = int(cpus)
        gpus = options.get('--gpus', '0')
        if not gpus.isdigit():
            raise SystemExit('Priority must be an integer number')

        self.gpus = int(gpus)

    def run(self):

        payload = json.dumps({
            'type': self.type,
            'priority': self.priority,
            'jobs': self.payload,
            'requisitions': [
                {'type': 'CPU', 'quantity': self.cpus},
                {'type': 'GPU', 'quantity': self.gpus},
            ]
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


class JobStatus(AbstractRequest):

    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        self.endpoint = JOB_INFO_ENDPOINT

        uuid = options.get('--uuid')
        if uuid:
            self.endpoint = Endpoint(path='/job/%s' % uuid, method='GET')

    def run(self):
        self.request(self.endpoint)


class AtlasStatus(AbstractRequest):

    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        self.endpoint = ATLAS_STATUS_ENDPOINT

    def run(self):
        self.request(self.endpoint)
