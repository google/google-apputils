#!/usr/bin/env python
#
# Copyright 2003 Google Inc. All Rights Reserved.

"""Unittest for shellutil module."""


__pychecker__ = '--unusednames=e,_'

import os

from google.apputils import basetest
from google.apputils import shellutil

# Running windows?
win32 = (os.name == 'nt')


class ShellUtilUnitTest(basetest.TestCase):
  def testShellEscapeList(self):
    # TODO(user): Actually run some shell commands and test the
    # shell escaping works properly.
    # Empty list
    words = []
    self.assertEquals(shellutil.ShellEscapeList(words), '')

    # Empty string
    words = ['']
    self.assertEquals(shellutil.ShellEscapeList(words), "''")

    # Single word
    words = ['foo']
    self.assertEquals(shellutil.ShellEscapeList(words), "'foo'")

    # Single word with single quote
    words = ["foo'bar"]
    expected = """   'foo'"'"'bar'   """.strip()
    self.assertEquals(shellutil.ShellEscapeList(words), expected)
    # .. double quote
    words = ['foo"bar']
    expected = """   'foo"bar'   """.strip()
    self.assertEquals(shellutil.ShellEscapeList(words), expected)

    # Multiple words
    words = ['foo', 'bar']
    self.assertEquals(shellutil.ShellEscapeList(words), "'foo' 'bar'")

    # Words with spaces 
    words = ['foo', 'bar', "foo'' ''bar"]
    expected = """   'foo' 'bar' 'foo'"'"''"'"' '"'"''"'"'bar'   """.strip()
    self.assertEquals(shellutil.ShellEscapeList(words), expected)

    # Now I'm just being mean
    words = ['foo', 'bar', """   ""'"'"   """.strip()]
    expected = """   'foo' 'bar' '""'"'"'"'"'"'"'   """.strip()
    self.assertEquals(shellutil.ShellEscapeList(words), expected)

  def testShellifyStatus(self):
    if not win32:
      self.assertEqual(shellutil.ShellifyStatus(0), 0)
      self.assertEqual(shellutil.ShellifyStatus(1), 129)
      self.assertEqual(shellutil.ShellifyStatus(1 * 256), 1)


if __name__ == '__main__':
  basetest.main()
