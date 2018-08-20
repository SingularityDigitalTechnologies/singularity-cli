"""
singularity-cli
Usage:
  singularity-cli ping [--api-url=<api_url>]
  singularity-cli atlas status --api-key=<api_key> --secret=<secret> [--api-url=<api_url>]
  singularity-cli batch add <payload> --type=<type> --priority=<priority> --api-key=<api_key> --secret=<secret> --cpus=<cpus> [--gpus=<gpus>] [--api-url=<api_url>]
  singularity-cli (job|batch) status --api-key=<api_key> --secret=<secret> [--api-url=<api_url>] [--uuid=<uuid>]
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


import sys

from docopt import docopt

from . import __version__ as VERSION

from singularity.commands.api import AtlasStatus
from singularity.commands.api import BatchAdd
from singularity.commands.api import BatchStatus
from singularity.commands.api import Ping
from singularity.commands.api import JobStatus


def main():
    options = docopt(__doc__, version=VERSION)

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

    if not cmd:
        print('Unknown option')
        sys.exit(1)

    cmd.run()
