#!/usr/bin/env python
# Copyright 2010 Google Inc. All Rights Reserved.

"""Tests for google.apputils.

In addition to the test modules under this package, we have a special TestCase
that runs the tests that are shell scripts.
"""

# TODO(dborowitz): It may be useful to generalize this and provide it to users
# who want to run their own sh_tests.

import os
import subprocess
import sys

from google.apputils import basetest
import gflags

FLAGS = gflags.FLAGS


class ShellScriptTests(basetest.TestCase):
  """TestCase that runs the various *test.sh scripts."""

  def RunTestScript(self, script_name):
    tests_path = os.path.dirname(__file__)
    sh_test_path = os.path.realpath(os.path.join(tests_path, script_name))
    path_with_python = ':'.join((
        os.path.dirname(sys.executable), os.environ.get('PATH')))

    env = {
        'PATH': path_with_python,
        # Setuptools puts dependency eggs in our path, so propagate that.
        'PYTHONPATH': os.pathsep.join(sys.path),
        'TEST_TMPDIR': FLAGS.test_tmpdir,
        }
    p = subprocess.Popen(sh_test_path, cwd=tests_path, env=env)
    self.assertEqual(0, p.wait())

  def testBaseTest(self):
    self.RunTestScript('basetest_sh_test.sh')

  def testApp(self):
    self.RunTestScript('app_unittest.sh')

  def testAppCommands(self):
    self.RunTestScript('appcommands_unittest.sh')


if __name__ == '__main__':
  basetest.main()
