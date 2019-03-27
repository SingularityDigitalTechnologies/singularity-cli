"""Packaging settings."""


from codecs import open
from os.path import abspath
from os.path import dirname
from os.path import join
from subprocess import call

from setuptools import Command
from setuptools import setup

from singularity import __version__


this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


class RunTests(Command):
    """Run all tests."""
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call(['py.test', '--cov-report=term-missing'])
        raise SystemExit(errno)


setup(
    name='singularity-cli',
    version=__version__,
    description='A CLI to run common singularity tasks.',
    long_description=long_description,
    url='https://github.com/SingularityDigitalTechnologies/singularity-cli',
    author='Sam Lacey',
    author_email='sam.lacey@singularity-technologies.io',
    license='MIT',
    keywords='cli',
    packages=['singularity', 'singularity.commands'],
    install_requires=[
        'docopt==0.6.2',
        'requests==2.18.4',
        'pytest==3.4.2',
        'mock==2.0.0',
    ],
    extras_require={'test': ['coverage', 'pytest', 'pytest-cov']},
    entry_points='''
        [console_scripts]
        singularity-cli=singularity.singularity:main
    ''',
    cmdclass={'test': RunTests},
)
