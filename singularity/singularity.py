"""
singularity-cli
Usage:
  singularity-cli ping [--api-url=<api_url>]
  singularity-cli batch add <payload> --type=<type> --priority=<priority> --api-key=<api_key> --secret=<secret> [--api-url=<api_url>]
  singularity-cli batch status --api-key=<api_key> --secret=<secret> [--api-url=<api_url>] [--uuid=<uuid>]
  singularity-cli -h | --help
  singularity-cli --version

Options:
  --api-url=<api_url>   URL to send requests to [default: https://api.singularity-technologies.io]
  -h --help             Show this screen.
  --version             Show version.

Examples:

Help:
  For help using this tool, please open an issue on the repository:
"""


import sys

from docopt import docopt

from . import __version__ as VERSION

from singularity.commands.api import BatchAdd
from singularity.commands.api import BatchStatus
from singularity.commands.api import Ping


def main():
    options = docopt(__doc__, version=VERSION)

    cmd = None
    if options.get('ping'):
        cmd = Ping(options)

    elif options.get('batch') and options.get('add'):
        cmd = BatchAdd(options)

    elif options.get('batch') and options.get('status'):
        cmd = BatchStatus(options)

    if not cmd:
        print('Unknown option')
        sys.exit(1)

    cmd.run()
