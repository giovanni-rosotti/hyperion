"""
This module prvoides the tools used to internally run the Hyperion test suite
from the installed version. It makes use of the `pytest` testing framework,
and is adapted from Astropy.
"""

import shlex
import sys
import os
import subprocess

from distutils.core import Command


class TestRunner(object):

    def __init__(self, base_path):
        self.base_path = base_path

    def run_tests(self, package=None, test_path=None, args=None, plugins=None,
                  verbose=False, pastebin=None, generate_reference=False,
                  bit_level_tests=False):

        if package is None:
            package_path = self.base_path
        else:
            package_path = os.path.join(self.base_path,
                                        package.replace('.', os.path.sep))

            if not os.path.isdir(package_path):
                raise ValueError('Package not found: {0}'.format(package))

        if test_path:
            package_path = os.path.join(package_path,
                                        os.path.abspath(test_path))

        all_args = package_path

        # add any additional args entered by the user
        if args is not None:
            all_args += ' {0}'.format(args)

        # add verbosity flag
        if verbose:
            all_args += ' -v'

        # turn on pastebin output
        if pastebin is not None:
            if pastebin in ['failed', 'all']:
                all_args += ' --pastebin={0}'.format(pastebin)
            else:
                raise ValueError("pastebin should be 'failed' or 'all'")

        if generate_reference:
            if generate_reference.startswith('-'):
                raise Exception("Need to specify output directory for generating reference files")
            if not generate_reference.startswith('/'):
                raise Exception("Need to specify output directory for generating reference files as an absolute path")
            all_args += ' --generate-reference={0}'.format(generate_reference)
            all_args += ' --enable-bit-level-tests'

        if bit_level_tests:
            all_args += ' --enable-bit-level-tests'

        all_args = shlex.split(all_args,
                               posix=not sys.platform.startswith('win'))

        import pytest
        return pytest.main(args=all_args, plugins=plugins)


class HyperionTest(Command, object):

    user_options = [
        ('package=', 'P',
         "The name of a specific package to test, e.g. 'model' or "
         "'densities'. If nothing is specified all default Hyperion tests "
         "are run."),
        ('test-path=', 't', 'Specify a test location by path. Must be '
         'specified absolutely or relative to the current directory. '
         'May be a single file or directory.'),
        ('verbose', 'V',
         'Turn on verbose output from pytest. Same as specifying `-v` in '
         '`args`.'),
        ('plugins=', 'p',
         'Plugins to enable when running pytest.  Same as specifying `-p` in '
         '`args`.'),
        ('pastebin=', 'b',
         "Enable pytest pastebin output. Either 'all' or 'failed'."),
        ('generate-reference=', 'g', "generate reference results for bit-level tests"),
        ('enable-bit-level-tests', 'l', "enable bit-level tests"),
        ('args=', 'a', 'Additional arguments to be passed to pytest'),
    ]

    def __init__(self, dist):
        Command.__init__(self, dist)
        self.verbose = False  # __init__ sets verbose to True after calling initialize_options

    def initialize_options(self):
        self.package = None
        self.test_path = None
        self.verbose = False
        self.plugins = None
        self.pastebin = None
        self.generate_reference = False
        self.enable_bit_level_tests = False
        self.args = None

    def finalize_options(self):
        pass

    def run(self):
        self.reinitialize_command('build')
        self.run_command('build')
        build_cmd = self.get_finalized_command('build')
        new_path = os.path.abspath(build_cmd.build_lib)

        if self.generate_reference:
            self.generate_reference = os.path.abspath(self.generate_reference)
            if not os.path.exists(self.generate_reference):
                raise IOError("Directory {0} does not exist".format(self.generate_reference))

        # Run the tests in a subprocess--this is necessary since new extension
        # modules may have appeared, and this is the easiest way to set up a
        # new environment
        cmd = ('import hyperion, sys; sys.exit(hyperion.test({0!r}, {1!r}, '
               '{2!r}, {3!r}, {4!r}, {5!r}, {6!r}, {7!r}))')
        cmd = cmd.format(self.package, self.test_path, self.args,
                         self.plugins, self.verbose, self.pastebin,
                         self.generate_reference, self.enable_bit_level_tests)

        raise SystemExit(subprocess.call([sys.executable, '-c', cmd],
                                         cwd=new_path, close_fds=False))
