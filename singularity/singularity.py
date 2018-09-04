"""
singularity-cli
Usage:
  singularity-cli ping [--api-url=<api_url>]
  singularity-cli atlas status [--api-key=<api_key> --secret=<secret> --api-url=<api_url>]
  singularity-cli hmac new <email> [--api-key=<api_key> --secret=<secret> --api-url=<api_url>]
  singularity-cli batch add <payload> --type=<type> --priority=<priority> --cpus=<cpus> --image=<image> --image-tag=<image_tag> [--api-key=<api_key> --secret=<secret> --gpus=<gpus> --api-url=<api_url>]
  singularity-cli (job|batch) status [--api-key=<api_key> --secret=<secret> --api-url=<api_url> --uuid=<uuid>]
  singularity-cli -h | --help
  singularity-cli --version

Options:
  --cpus=<cpus>         Number of CPUs required for each job
  --gpus=<gpus>         Number of GPUs required for each job
  --priority=<priority> Priority of job [default: 2]
  --api-url=<api_url>   URL to send requests to [default: https://api.singularity-technologies.io]
  -h --help             Show this screen.
  --version             Show version.

Examples:
  singularity-cli batch add '[{"a": 14, "b": "27"}]' --type pythagoras --priority 0 --api-key=key --secret=secret
  singularity-cli batch status --uuid=some-unique-id --api-key=key --secret=secret

Help:
  For help using this tool, please open an issue on the repository:
"""


import json
import os
import sys

from docopt import docopt

from . import __version__ as VERSION

from singularity.commands.api import AtlasStatus
from singularity.commands.api import BatchAdd
from singularity.commands.api import BatchStatus
from singularity.commands.api import GenerateHMAC
from singularity.commands.api import Ping
from singularity.commands.api import JobStatus


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

    cmd = None
    if options.get('ping'):
        cmd = Ping(options)

    elif options.get('batch') and options.get('add'):
        cmd = BatchAdd(options)

    elif options.get('batch') and options.get('status'):
        cmd = BatchStatus(options)

    elif options.get('job') and options.get('status'):
        cmd = JobStatus(options)

    elif options.get('atlas') and options.get('status'):
        cmd = AtlasStatus(options)

    elif options.get('hmac') and options.get('new'):
        cmd = GenerateHMAC(options)

    if not cmd:
        print('Unknown option')
        sys.exit(1)

    cmd.run()
