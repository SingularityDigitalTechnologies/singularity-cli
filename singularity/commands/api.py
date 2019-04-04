import datetime
import hmac
import json
import os
import pprint
import requests

from collections import namedtuple
from hashlib import sha512
from urllib.parse import urlparse
from urllib.parse import urlunparse

from requests import Request
from requests import Session

from singularity.commands.base import Command
from singularity.commands.data import Sharder


Endpoint = namedtuple('Endpoint', ['path', 'method'])

PING_ENDPOINT = Endpoint(path='/ping', method='GET')

ATLAS_STATUS_ENDPOINT = Endpoint(path='/status', method='GET')
BATCH_INFO_ENDPOINT = Endpoint(path='/batch', method='GET')
BATCH_CREATE_ENDPOINT = Endpoint(path='/batch', method='POST')
JOB_INFO_ENDPOINT = Endpoint(path='/job', method='GET')

GENERATE_HMAC = Endpoint(path='/sec/key', method='POST')
USER_ADD = Endpoint(path='/user', method='POST')
COMPANY_ADD = Endpoint(path='/company', method='POST')
DATASET_ADD = Endpoint(path='/data', method='POST')
CHUNK_ADD = Endpoint(path='/data/%s/chunk', method='POST')


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
        self.print_response(payload, response)
        return payload

    def print_response(self, payload, response):
        pprint.PrettyPrinter(indent=4).pprint(payload or response.text)


class Ping(AbstractRequest):

    def run(self):
        self.request(PING_ENDPOINT)


class BatchCreate(AbstractRequest):

    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        self.payload = ''
        payload_file = options.get('<payload_file>', '')
        if not os.path.exists(payload_file):
            raise SystemExit('"%s" is not a valid file' % payload_file)

        with open(payload_file, 'r') as f:
            try:
                self.payload = json.load(f)
            except ValueError:
                raise SystemExit('Payload not JSON decodable')

        self.mode = options.get('--mode', '')
        if not self.mode:
            raise SystemExti('Mode must be set to either Pilot or Production')

        cpus = options.get('--cpus') or '0'
        if not cpus.isdigit():
            raise SystemExit('CPUS must be an integer number')

        self.cpus = int(cpus)
        gpus = options.get('--gpus') or '0'
        if not gpus.isdigit():
            raise SystemExit('GPUS must be an integer number')

        self.gpus = int(gpus)

    def run(self):

        payload = json.dumps({
            'mode': self.mode,
            'jobs': self.payload,
            'requisitions': {
                'cpu': {'kind': 'cpu', 'quantity': self.cpus},
                'gpu': {'kind': 'gpu', 'quantity': self.gpus},
            }
        })

        self.request(BATCH_CREATE_ENDPOINT, payload)


class BatchStatus(AbstractRequest):

    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        self.endpoint = BATCH_INFO_ENDPOINT

        uuid = options.get('--uuid')
        if uuid:
            self.endpoint = Endpoint(path='/batch/%s' % uuid, method='GET')

    def run(self):
        self.request(self.endpoint)


class BatchSummary(AbstractRequest):

    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        self.endpoint = BATCH_INFO_ENDPOINT

        self.since = None
        since = options.get('--since')
        if since:
            self.since = datetime.datetime.strptime(since, '%Y-%m-%d')

    def run(self):
        self.request(self.endpoint)

    def print_response(self, payload, response):
        if payload:
            for _, batches in payload.items():
                for batch in batches:
                    uuid = batch.get('uuid', '')
                    status = batch.get('status', '')
                    started = batch.get('created_at', '')
                    if not self.since:
                        print('%s, %s: %s' % (uuid, started, status))
                        continue

                    started_datetime = datetime.datetime.strptime(started, '%Y-%m-%dT%H:%M:%S.%fZ')
                    if started_datetime >= self.since:
                        print('%s, %s: %s' % (uuid, started, status))


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


class GenerateHMAC(AbstractRequest):

    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        self.email = options.get('<email>')
        self.endpoint = GENERATE_HMAC

    def run(self):
        self.request(self.endpoint, json.dumps({'email': self.email}))


class UserAdd(AbstractRequest):
    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        self.first_name = options.get('<first_name>', '')
        self.last_name = options.get('<last_name>', '')
        self.email = options.get('<email>', '')
        self.user_type = options.get('--user-type', '').lower()
        self.password = options.get('--password', '')

        self.endpoint = USER_ADD

    def run(self):
        self.request(
            self.endpoint,
            json.dumps({
                'first_name': self.first_name,
                'last_name': self.last_name,
                'email': self.email,
                'user_type': self.user_type,
                'password': self.password,
            })
        )


class CompanyAdd(AbstractRequest):
    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        self.name = options.get('<name>')
        self.endpoint = COMPANY_ADD

    def run(self):
        self.request(self.endpoint, json.dumps({'name': self.name}))


class DataSetAdd(AbstractRequest):
    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

        self.name = options.get('<name>')
        location = options.get('<location>')
        if not location:
            raise SystemExit('Location not defined')

        imprint_location = options.get('<imprint_location>')
        if not imprint_location:
            raise SystemExit('Imprint location not defined')

        pilot_count = options.get('--pilot-count', 0)
        if not pilot_count:
            raise SystemExit('Pilot Count not defined')

        if not pilot_count.isdigit():
            raise SystemExit('Pilot Count must be an integer')

        self.pilot_count = int(pilot_count)

        self.dataset_endpoint = DATASET_ADD
        self.chunk_endpoint = CHUNK_ADD

        sharder = Sharder(location, imprint_location)
        for shard_id, shard in sharder.get_new_shards():
            print(shard_id, len(shard))

        boop

    def run(self):
        request_payload = json.dumps({
            'name': self.name,
            'pilot_count': self.pilot_count
        })

        payload = self.request(self.dataset_endpoint, request_payload)
        print(payload)
