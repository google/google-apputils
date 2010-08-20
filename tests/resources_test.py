#!/usr/bin/env python
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the resources module."""

__author__ = 'dborowitz@google.com (Dave Borowitz)'

from google.apputils import basetest

from google.apputils import file_util
from google.apputils import resources

PREFIX = __name__ + ':data/'


class ResourcesTest(basetest.TestCase):

  def _CheckTestData(self, func):
    self.assertEqual('test file a contents\n', func(PREFIX + 'a'))
    self.assertEqual('test file b contents\n', func(PREFIX + 'b'))

  def testGetResource(self):
    self._CheckTestData(resources.GetResource)

  def testGetResourceAsFile(self):
    self._CheckTestData(lambda n: resources.GetResourceAsFile(n).read())

  def testGetResourceFilename(self):
    self._CheckTestData(
        lambda n: file_util.Read(resources.GetResourceFilename(n)))


if __name__ == '__main__':
  basetest.main()
