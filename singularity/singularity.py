"""
singularity-cli
Usage:
  singularity-cli ping [--api-url=<api_url>]
  singularity-cli batch create --payload-file=<payload_file> --cpus=<cpus> --mode=<mode> [--api-key=<api_key> --secret=<secret> --gpus=<gpus> --api-url=<api_url>]
  singularity-cli (job|batch) status <uuid> [--api-key=<api_key> --secret=<secret> --api-url=<api_url>]
  singularity-cli (job|batch) cancel <uuid> [--api-key=<api_key> --secret=<secret> --api-url=<api_url>]
  singularity-cli batch summary [--api-key=<api_key> --secret=<secret> --api-url=<api_url> --since=<since>]
  singularity-cli dataset add <name> <location> <imprint_location> --pilot-count=<pilot_count> [--api-key=<api_key> --secret=<secret> --api-url=<api_url>]
  singularity-cli dataset summary <name> [--api-key=<api_key> --secret=<secret> --api-url=<api_url>]
  singularity-cli model download <batch_uuid> <job_uuid> --download-path=<download_path> [--api-key=<api_key> --secret=<secret> --api-url=<api_url>]
  singularity-cli -h | --help
  singularity-cli --version

Options:
  --cpus=<cpus>                    Number of CPUs required for each job (can be fractional)
  --gpus=<gpus>                    Number of GPUs required for each job
  --payload-file=<payload_file>    Path to a json file listing ML experiments you wish to run
  --mode=<mode>                    Mode of operation (pilot|production)
  --api-url=<api_url>              URL to send requests to [default: https://api.singularity-technologies.io]

  -h --help                        Show this screen.
  --version                        Show version.
"""

import json
import os
import sys

from docopt import docopt

from . import __version__ as VERSION

from singularitytechnologiesapi import BatchCreate
from singularitytechnologiesapi import BatchStatus
from singularitytechnologiesapi import BatchSummary
from singularitytechnologiesapi import Cancel
from singularitytechnologiesapi import Ping
from singularitytechnologiesapi import JobStatus
from singularitytechnologiesapi import DataSetAdd
from singularitytechnologiesapi import DataSetSummary
from singularitytechnologiesapi import ModelDownload


def __load_config():
    home = os.environ.get('HOME')
    default_path = os.path.join(home, '.singularity')

    # Attempt to get path override
    config_path = os.environ.get('SINGULARITY_CONFIG_PATH', default_path)
    config_file = os.path.join(config_path, 'config.json')

    if not os.path.exists(config_file):
        print('No config file detected at: "%s"' % config_file)
        return {}

    config = {}
    with open(config_file, 'r') as f:
        try:
            config = json.load(f)

        except ValueError as e:
            raise SystemExit(
                'Config file "%s" is not valid json: %s' % (config_file, e)
            )

    return config


def main():
    config = __load_config()
    options = docopt(__doc__, version=VERSION)

    options['--api-key'] = options['--api-key'] or config.pop('api_key', '')
    options['--secret'] = options['--secret'] or config.pop('secret', '')

    if not options.get('--api-key'):
        raise SystemExit('API Key not set in either arguents or config file')

    if not options.get('--secret'):
        raise SystemExit('Secret not set in either arguents or config file')

    new_options = {}
    for key, value in options.items():
        key = key.replace('--', '')
        key = key.replace('-', '_')
        key = key.replace('<', '')
        key = key.replace('>', '')

        new_options[key] = value

    options = new_options

    cmd = None
    if options.get('ping'):
        cmd = Ping(options)

    elif options.get('batch') and options.get('create'):
        with open(options.get('payload_file', 'r')) as f:
            options['payload'] = json.load(f)

        cmd = BatchCreate(options)

    elif options.get('batch') and options.get('status'):
        cmd = BatchStatus(options)

    elif options.get('batch') and options.get('summary'):
        cmd = BatchSummary(options)

    elif options.get('job') and options.get('status'):
        cmd = JobStatus(options)

    elif options.get('job') and options.get('cancel'):
        cmd = Cancel(options, 'job')

    elif options.get('batch') and options.get('cancel'):
        cmd = Cancel(options, 'batch')

    elif options.get('atlas') and options.get('status'):
        cmd = AtlasStatus(options)

    elif options.get('dataset') and options.get('add'):
        cmd = DataSetAdd(options)

    elif options.get('dataset') and options.get('summary'):
        cmd = DataSetSummary(options)

    elif options.get('model') and options.get('download'):
        cmd = ModelDownload(options)

    if not cmd:
        print('Unknown option')
        sys.exit(1)

    try:
        payload, status_code = cmd.run()
    except Exception as e:
        print('Command Error: %s' % e)
        return

    cmd.summary()
