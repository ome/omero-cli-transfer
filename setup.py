import os
import sys
from setuptools import setup
from setuptools.command.test import test as test_command

with open("README.md", "r") as fh:
    long_description = fh.read()


class PyTest(test_command):
    user_options = [
        ('test-path=', 't', "base dir for test collection"),
        ('test-ice-config=', 'i',
         "use specified 'ice config' file instead of default"),
        ('test-pythonpath=', 'p', "prepend 'pythonpath' to PYTHONPATH"),
        ('test-marker=', 'm', "only run tests including 'marker'"),
        ('test-no-capture', 's', "don't suppress test output"),
        ('test-failfast', 'x', "Exit on first error"),
        ('test-verbose', 'v', "more verbose output"),
        ('test-quiet', 'q', "less verbose output"),
        ('junitxml=', None, "create junit-xml style report file at 'path'"),
        ('pdb', None, "fallback to pdb on error"),
        ]

    def initialize_options(self):
        test_command.initialize_options(self)
        self.test_pythonpath = None
        self.test_string = None
        self.test_marker = None
        self.test_path = 'test'
        self.test_failfast = False
        self.test_quiet = False
        self.test_verbose = False
        self.test_no_capture = False
        self.junitxml = None
        self.pdb = False
        self.test_ice_config = None

    def finalize_options(self):
        test_command.finalize_options(self)
        self.test_args = [self.test_path]
        if self.test_string is not None:
            self.test_args.extend(['-k', self.test_string])
        if self.test_marker is not None:
            self.test_args.extend(['-m', self.test_marker])
        if self.test_failfast:
            self.test_args.extend(['-x'])
        if self.test_verbose:
            self.test_args.extend(['-v'])
        if self.test_quiet:
            self.test_args.extend(['-q'])
        if self.junitxml is not None:
            self.test_args.extend(['--junitxml', self.junitxml])
        if self.pdb:
            self.test_args.extend(['--pdb'])
        self.test_suite = True
        if 'ICE_CONFIG' not in os.environ:
            os.environ['ICE_CONFIG'] = self.test_ice_config

    def run_tests(self):
        if self.test_pythonpath is not None:
            sys.path.insert(0, self.test_pythonpath)
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


def read(fname):
    """
    Utility function to read the README file.
    :rtype : String
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    packages=['', 'omero.plugins'],
    package_dir={"": "src"},
    name="omero-cli-transfer",
    version=os.environ.get('VERSION', '0.0.0'),
    maintainer="Erick Ratamero",
    maintainer_email="erick.ratamero@jax.org",
    description=("A set of utilities for exporting a transfer"
                 " packet from an OMERO server and importing "
                 "it in a different server. Developed by the "
                 "Research IT team at The Jackson Laboratory."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TheJacksonLaboratory/omero-cli-transfer",
    install_requires=[
        'ezomero',
        'ome-types'
    ],
    python_requires='>=3.7',
    cmdclass={'test': PyTest},
    tests_require=['pytest', 'restview', 'mox3'],
)
