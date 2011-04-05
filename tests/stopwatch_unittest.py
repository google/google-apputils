#!/usr/bin/env python
# Copyright 2006 Google Inc. All Rights Reserved.
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

"""Tests for the stopwatch module."""

__author__ = 'dbentley@google.com (Dan Bentley)'

from google.apputils import basetest

import gflags as flags
from google.apputils import stopwatch

FLAGS = flags.FLAGS


class StubTime(object):
  """Simple stub replacement for the time module.

  Only useful for relative calculations, since it always starts at 0.
  """
  # These method names match the standard library time module.

  def __init__(self):
    self._counter = 0

  def time(self):
    """Get the time for this time object.

    A call is always guaranteed to be greater than the previous one.

    Returns:
      A monotonically increasing time.
    """
    self._counter += 0.0001
    return self._counter

  def sleep(self, time):
    """Simulate sleeping for the specified number of seconds."""
    self._counter += time


class StopwatchUnitTest(basetest.TestCase):
  """Stopwatch tests.

  These tests are tricky because timing is difficult.

  Therefore, we test the structure of the results but not the results
  themselves for fear it would lead to intermittent but persistent
  failures.
  """

  def setUp(self):
    self.time = StubTime()
    stopwatch.time = self.time

  def testResults(self):
    sw = stopwatch.StopWatch()
    sw.start()
    sw.stop()

    results = sw.results()

    self.assertListEqual([r[0] for r in results], ['total'])

    results = sw.results(verbose=1)
    self.assertListEqual([r[0] for r in results], ['overhead', 'total'])

    # test tally part of results.
    sw.start('ron')
    sw.stop('ron')
    sw.start('ron')
    sw.stop('ron')
    results = sw.results()
    results = sw.results(verbose=1)
    for r in results:
      if r[0] == 'ron':
        assert r[2] == 2

  def testSeveralTimes(self):
    sw = stopwatch.StopWatch()
    sw.start()

    sw.start('a')
    sw.start('b')
    self.time.sleep(1)
    sw.stop('b')
    sw.stop('a')

    sw.stop()

    results = sw.results(verbose=1)
    self.assertListEqual([r[0] for r in results],
                         ['a', 'b', 'overhead', 'total'])

    # Make sure overhead is positive
    self.assertEqual(results[2][1] > 0, 1)

  def testNoStopOthers(self):
    sw = stopwatch.StopWatch()
    sw.start()

    sw.start('a')
    sw.start('b', stop_others=0)
    self.time.sleep(1)
    sw.stop('b')
    sw.stop('a')

    sw.stop()

    #overhead should be negative, because we ran two timers simultaneously
    #It is possible that this could fail in outlandish circumstances.
    #If this is a problem in practice, increase the value of the call to
    #time.sleep until it passes consistently.
    #Or, consider finding a platform where the two calls sw.start() and
    #sw.start('a') happen within 1 second.
    results = sw.results(verbose=1)
    self.assertEqual(results[2][1] < 0, 1)

  def testStopNonExistentTimer(self):
    sw = stopwatch.StopWatch()
    self.assertRaises(RuntimeError, sw.stop)
    self.assertRaises(RuntimeError, sw.stop, 'foo')

  def testResultsDoesntCrashWhenUnstarted(self):
    sw = stopwatch.StopWatch()
    sw.results()

  def testResultsDoesntCrashWhenUnstopped(self):
    sw = stopwatch.StopWatch()
    sw.start()
    sw.results()

  def testTimerValue(self):
    sw = stopwatch.StopWatch()
    self.assertAlmostEqual(0, sw.timervalue('a'), 2)
    sw.start('a')
    self.assertAlmostEqual(0, sw.timervalue('a'), 2)
    self.time.sleep(1)
    self.assertAlmostEqual(1, sw.timervalue('a'), 2)
    sw.stop('a')
    self.assertAlmostEqual(1, sw.timervalue('a'), 2)
    sw.start('a')
    self.time.sleep(1)
    self.assertAlmostEqual(2, sw.timervalue('a'), 2)
    sw.stop('a')
    self.assertAlmostEqual(2, sw.timervalue('a'), 2)

  def testResultsDoesntReset(self):
    sw = stopwatch.StopWatch()
    sw.start()
    self.time.sleep(1)
    sw.start('a')
    self.time.sleep(1)
    sw.stop('a')
    sw.stop()
    res1 = sw.results(verbose=True)
    res2 = sw.results(verbose=True)
    self.assertListEqual(res1, res2)


if __name__ == '__main__':
  basetest.main()
