# Google Application Utilities for Python #

This project is a small collection of utilities for building Python
applications.  It includes some of the same set of utilities used to build and
run internal Python apps at Google.

Features:

  * Simple application startup integrated with [python-gflags](http://code.google.com/p/python-gflags).
  * Subcommands for command-line applications.
  * Option to drop into [pdb](http://docs.python.org/library/pdb.html) on uncaught exceptions.
  * Helper functions for dealing with files.
  * High-level profiling tools.
  * Timezone-aware wrappers for `datetime.datetime` classes.
  * Improved `TestCase` with many of the same methods as [unittest2](http://pypi.python.org/pypi/unittest2), plus helpful flags for test startup.
  * `google_test` setuptools command for running tests.
  * Helper module for creating application stubs.