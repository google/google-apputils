Google Application Utilities for Python
=======================================

This project is a small collection of utilities for building Python
applications.  It includes some of the same set of utilities used to build and
run internal Python apps at Google.

Features:

  * Simple application startup integrated with python-gflags.
  * Subcommands for command-line applications.
  * Option to drop into pdb on uncaught exceptions.
  * Helper functions for dealing with files.
  * High-level profiling tools.
  * Timezone-aware wrappers for datetime.datetime classes.
  * Improved TestCase with the same methods as unittest2, plus helpful flags for
    test startup.
  * google_test setuptools command for running tests.
  * Helper module for creating application stubs.


Installation
============

To install the package, simply run:
  python setup.py install


Google-Style Tests
==================

Google-style tests (those run with basetest.main()) differ from setuptools-style
tests in that test modules are designed to be run as __main__. Setting up your
project to use Google-style tests is easy:

1. Create one or more test modules named '*_test.py' in a directory. Each test
module should have a main block that runs basetest.main():
  # In tests/my_test.py
  from google.apputils import basetest

  class MyTest(basetest.TestCase):
    def testSomething(self):
      self.assertTrue('my test')

  if __name__ == '__main__':
    basetest.main()

2. Add a setup requirement on google-apputils and set the test_dir option:
  # In setup.py
  setup(
      ...
      setup_requires = ['google-apputils>=0.2'],
      test_dir = 'tests',
      )

3. Run your tests:
  python setup.py google_test


Google-Style Stub Scripts
=========================

Google-style binaries (run with app.run()) are intended to be executed directly
at the top level, so you should not use a setuptools console_script entry point
to point at your main(). You can use distutils-style scripts if you want.

Another alternative is to use google.apputils.run_script_module, which is a
handy wrapper to execute a module directly as if it were a script:

1. Create a module like 'stubs.py' in your project:
  # In my/stubs.py
  from google.apputils import run_script_module

  def RunMyScript():
    import my.script
    run_script_module.RunScriptModule(my.script)

  def RunMyOtherScript():
    import my.other_script
    run_script_module.RunScriptModule(my.other_script)

2. Set up entry points in setup.py that point to the functions in your stubs
module:
  # In setup.py
  setup(
      ...
      entry_points = {
          'console_scripts': [
              'my_script = my.stubs:RunMyScript',
              'my_other_script = my.stubs.RunMyOtherScript',
              ],
          },
      )

There are also useful flags you can pass to your scripts to help you debug your
binaries; run your binary with --helpstub to see the full list.
