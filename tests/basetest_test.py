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

"""Tests for base google test functionality."""

__author__ = 'dborowitz@google.com (Dave Borowitz)'

import os
import re
import sys
import unittest

import gflags as flags
from google.apputils import basetest

FLAGS = flags.FLAGS

flags.DEFINE_integer('testid', 0, 'Which test to run')


class GoogleTestBaseUnitTest(basetest.TestCase):
  def testCapturing(self):
    basetest.CaptureTestStdout()
    basetest.CaptureTestStderr()
    # print two lines to stdout
    sys.stdout.write('This goes to captured.out\n')
    sys.stdout.write('This goes to captured.out\n')
    sys.stderr.write('This goes to captured.err\n')

    stdout_filename = os.path.join(FLAGS.test_tmpdir, 'stdout.diff')
    stdout_file = open(stdout_filename, 'wb')
    stdout_file.write('This goes to captured.out\n'
                      'This goes to captured.out\n')
    stdout_file.close()
    basetest.DiffTestStdout(stdout_filename)

    # After DiffTestStdout(), the standard output is no longer captured
    # and is written to the screen. Standard error is still captured.
    sys.stdout.write('This goes to stdout screen 1/2\n')
    sys.stderr.write('This goes to captured.err\n')

    # After CaptureTestStdout(), both standard output and standard error
    # are captured.
    basetest.CaptureTestStdout()
    sys.stdout.write('This goes to captured.out\n')
    sys.stderr.write('This goes to captured.err\n')

    stderr_filename = os.path.join(FLAGS.test_tmpdir, 'stderr.diff')
    stderr_file = open(stderr_filename, 'wb')
    stderr_file.write('This goes to captured.err\n'
                      'This goes to captured.err\n'
                      'This goes to captured.err\n')
    stderr_file.close()

    # After DiffTestStderr(), the standard error is no longer captured and
    # is written to the screen. Standard output is still captured.
    basetest.DiffTestStderr(stderr_filename)
    sys.stdout.write('This goes to captured.out\n')
    sys.stderr.write('This goes to stderr screen 2/2\n')

    basetest.DiffTestStdout(stdout_filename)

    basetest.CaptureTestStdout()
    sys.stdout.write('Correct Output\n')
    stdout_filename = os.path.join(FLAGS.test_tmpdir, 'stdout.diff')
    stdout_file = open(stdout_filename, 'wb')
    stdout_file.write('Incorrect Output\n')
    stdout_file.close()
    self.assertRaises(basetest.OutputDifferedError, basetest.DiffTestStdout,
                      stdout_filename)

  def testFlags(self):
    if FLAGS.testid == 1:
      self.assertEqual(FLAGS.test_random_seed, 301)
      self.assert_(FLAGS.test_tmpdir.startswith('/'))
      self.assert_(os.access(FLAGS.test_tmpdir, os.W_OK))
    elif FLAGS.testid == 2:
      self.assertEqual(FLAGS.test_random_seed, 321)
      self.assertEqual(FLAGS.test_srcdir, 'cba')
      self.assertEqual(FLAGS.test_tmpdir, 'fed')
    elif FLAGS.testid == 3:
      self.assertEqual(FLAGS.test_random_seed, 123)
      self.assertEqual(FLAGS.test_srcdir, 'abc')
      self.assertEqual(FLAGS.test_tmpdir, 'def')
    elif FLAGS.testid == 4:
      self.assertEqual(FLAGS.test_random_seed, 123)
      self.assertEqual(FLAGS.test_srcdir, 'abc')
      self.assertEqual(FLAGS.test_tmpdir, 'def')

  def testAssertIn(self):
    animals = {'monkey': 'banana', 'cow': 'grass', 'seal': 'fish'}

    self.assertIn('a', 'abc')
    self.assertIn(2, [1, 2, 3])
    self.assertIn('monkey', animals)

    self.assertNotIn('d', 'abc')
    self.assertNotIn(0, [1, 2, 3])
    self.assertNotIn('otter', animals)

    self.assertRaises(AssertionError, self.assertIn, 'x', 'abc')
    self.assertRaises(AssertionError, self.assertIn, 4, [1, 2, 3])
    self.assertRaises(AssertionError, self.assertIn, 'elephant', animals)

    self.assertRaises(AssertionError, self.assertNotIn, 'c', 'abc')
    self.assertRaises(AssertionError, self.assertNotIn, 1, [1, 2, 3])
    self.assertRaises(AssertionError, self.assertNotIn, 'cow', animals)

  def testAssertEqual(self):
    if FLAGS.testid != 5:
      return

    self.assertListEqual([], [])
    self.assertTupleEqual((), ())
    self.assertSequenceEqual([], ())

    a = [0, 'a', []]
    b = []
    self.assertRaises(basetest.TestCase.failureException,
                      self.assertListEqual, a, b)
    self.assertRaises(basetest.TestCase.failureException,
                      self.assertListEqual, tuple(a), tuple(b))
    self.assertRaises(basetest.TestCase.failureException,
                      self.assertSequenceEqual, a, tuple(b))

    b.extend(a)
    self.assertListEqual(a, b)
    self.assertTupleEqual(tuple(a), tuple(b))
    self.assertSequenceEqual(a, tuple(b))
    self.assertSequenceEqual(tuple(a), b)

    self.assertRaises(AssertionError, self.assertListEqual, a, tuple(b))
    self.assertRaises(AssertionError, self.assertTupleEqual, tuple(a), b)
    self.assertRaises(AssertionError, self.assertListEqual, None, b)
    self.assertRaises(AssertionError, self.assertTupleEqual, None, tuple(b))
    self.assertRaises(AssertionError, self.assertSequenceEqual, None, tuple(b))
    self.assertRaises(AssertionError, self.assertListEqual, 1, 1)
    self.assertRaises(AssertionError, self.assertTupleEqual, 1, 1)
    self.assertRaises(AssertionError, self.assertSequenceEqual, 1, 1)

    self.assertSameElements([1, 2, 3], [3, 2, 1])
    self.assertSameElements([1, 2] + [3] * 100, [1] * 100 + [2, 3])
    self.assertSameElements(['foo', 'bar', 'baz'], ['bar', 'baz', 'foo'])
    self.assertRaises(AssertionError, self.assertSameElements, [10], [10, 11])
    self.assertRaises(AssertionError, self.assertSameElements, [10, 11], [10])

    # Test that sequences of unhashable objects can be tested for sameness:
    self.assertSameElements([[1, 2], [3, 4]], [[3, 4], [1, 2]])
    self.assertSameElements([{'a': 1}, {'b': 2}], [{'b': 2}, {'a': 1}])
    self.assertRaises(AssertionError, self.assertSameElements, [[1]], [[2]])

  def testAssertDictEqual(self):
    self.assertDictEqual({}, {})

    c = {'x': 1}
    d = {}
    self.assertRaises(basetest.TestCase.failureException,
                      self.assertDictEqual, c, d)

    d.update(c)
    self.assertDictEqual(c, d)

    d['x'] = 0
    self.assertRaises(basetest.TestCase.failureException,
                      self.assertDictEqual, c, d, 'These are unequal')

    self.assertRaises(AssertionError, self.assertDictEqual, None, d)
    self.assertRaises(AssertionError, self.assertDictEqual, [], d)
    self.assertRaises(AssertionError, self.assertDictEqual, 1, 1)

    try:
      self.assertDictEqual({}, {'x': 1})
    except AssertionError, e:
      self.assertMultiLineEqual("{} != {'x': 1}\n"
                                "- {}\n"
                                "+ {'x': 1}",
                                str(e))
    else:
      self.fail('Expecting AssertionError')

    try:
      self.assertDictEqual({}, {'x': 1}, 'a message')
    except AssertionError, e:
      self.assertEqual("{} != {'x': 1}\n"
                       "- {}\n"
                       "+ {'x': 1} : a message", str(e))
    else:
      self.fail('Expecting AssertionError')

    try:
      self.assertDictEqual({'a': 1, 'b': 2, 'c': 3},
                           {'a': 2, 'c': 3, 'd': 4})
    except AssertionError, e:
      self.assertMultiLineEqual(
          '\n'.join(["{'a': 1, 'c': 3, 'b': 2} != {'a': 2, 'c': 3, 'd': 4}",
                     "- {'a': 1, 'b': 2, 'c': 3}",
                     "+ {'a': 2, 'c': 3, 'd': 4}"]),
          str(e))
    else:
      self.fail('Expecting AssertionError')

    self.assertRaises(AssertionError, self.assertDictEqual, (1, 2), {})
    self.assertRaises(AssertionError, self.assertDictEqual, {}, (1, 2))

  def testAssertSetEqual(self):
    set1 = set()
    set2 = set()
    self.assertSetEqual(set1, set2)

    self.assertRaises(AssertionError, self.assertSetEqual, None, set2)
    self.assertRaises(AssertionError, self.assertSetEqual, [], set2)
    self.assertRaises(AssertionError, self.assertSetEqual, set1, None)
    self.assertRaises(AssertionError, self.assertSetEqual, set1, [])

    set1 = set(['a'])
    set2 = set()
    self.assertRaises(AssertionError, self.assertSetEqual, set1, set2)

    set1 = set(['a'])
    set2 = set(['a'])
    self.assertSetEqual(set1, set2)

    set1 = set(['a'])
    set2 = set(['a', 'b'])
    self.assertRaises(AssertionError, self.assertSetEqual, set1, set2)

    set1 = set(['a'])
    set2 = frozenset(['a', 'b'])
    self.assertRaises(AssertionError, self.assertSetEqual, set1, set2)

    set1 = set(['a', 'b'])
    set2 = frozenset(['a', 'b'])
    self.assertSetEqual(set1, set2)

    set1 = set()
    set2 = 'foo'
    self.assertRaises(AssertionError, self.assertSetEqual, set1, set2)
    self.assertRaises(AssertionError, self.assertSetEqual, set2, set1)

    # make sure any string formatting is tuple-safe
    set1 = set([(0, 1), (2, 3)])
    set2 = set([(4, 5)])
    self.assertRaises(AssertionError, self.assertSetEqual, set1, set2)

  def testAssertDictContainsSubset(self):
    self.assertDictContainsSubset({}, {})

    self.assertDictContainsSubset({}, {'a': 1})

    self.assertDictContainsSubset({'a': 1}, {'a': 1})

    self.assertDictContainsSubset({'a': 1}, {'a': 1, 'b': 2})

    self.assertDictContainsSubset({'a': 1, 'b': 2}, {'a': 1, 'b': 2})

    self.assertRaises(basetest.TestCase.failureException,
                      self.assertDictContainsSubset, {'a': 2}, {'a': 1},
                      '.*Mismatched values:.*')

    self.assertRaises(basetest.TestCase.failureException,
                      self.assertDictContainsSubset, {'c': 1}, {'a': 1},
                      '.*Missing:.*')

    self.assertRaises(basetest.TestCase.failureException,
                      self.assertDictContainsSubset, {'a': 1, 'c': 1}, {'a': 1},
                      '.*Missing:.*')

    self.assertRaises(basetest.TestCase.failureException,
                      self.assertDictContainsSubset, {'a': 1, 'c': 1}, {'a': 1},
                      '.*Missing:.*Mismatched values:.*')

  def testAssertContainsSubset(self):
    # sets, lists, tuples, dicts all ok.  Types of set and subset do not have to
    # match.
    actual = ('a', 'b', 'c')
    self.assertContainsSubset(set(('a', 'b')), actual)
    self.assertContainsSubset(('b', 'c'), actual)
    self.assertContainsSubset({'b': 1, 'c': 2}, list(actual))
    self.assertContainsSubset(['c', 'a'], set(actual))
    self.assertContainsSubset([], set())
    self.assertContainsSubset([], {'a': 1})

    self.assertRaises(AssertionError, self.assertContainsSubset, ('d',), actual)
    self.assertRaises(AssertionError, self.assertContainsSubset, ['d'],
                      set(actual))
    self.assertRaises(AssertionError, self.assertContainsSubset, {'a': 1}, [])

    self.assertRaisesWithRegexpMatch(AssertionError, 'Missing elements',
                                     self.assertContainsSubset, set((1, 2, 3)),
                                     set((1, 2)))
    self.assertRaisesWithRegexpMatch(
        AssertionError, 'Custom message: Missing elements',
        self.assertContainsSubset, set((1, 2)), set((1,)), 'Custom message')

  def testAssertAlmostEqual(self):
    if FLAGS.testid != 6:
      return

    self.assertAlmostEqual(1.00000001, 1.0)
    self.assertNotAlmostEqual(1.0000001, 1.0)

  def testAssertAlmostEqualsWithDelta(self):
    self.assertAlmostEquals(3.14, 3, delta=0.2)
    self.assertAlmostEquals(2.81, 3.14, delta=1)
    self.assertAlmostEquals(-1, 1, delta=3)
    self.assertRaises(AssertionError, self.assertAlmostEquals,
                      3.14, 2.81, delta=0.1)
    self.assertRaises(AssertionError, self.assertAlmostEquals,
                      1, 2, delta=0.5)
    self.assertNotAlmostEquals(3.14, 2.81, delta=0.1)

  def testGetCommandString_listOfStringArgument(self):
    expected = "'command' 'arg-0'"

    observed = basetest.GetCommandString(['command', 'arg-0'])

    self.assertEqual(expected, observed)

  def testGetCommandString_listOfUnicodeStringArgument(self):
    expected = "'command' 'arg-0'"

    observed = basetest.GetCommandString([u'command', u'arg-0'])

    self.assertEqual(expected, observed)

  def testGetCommandString_stringArgument(self):
    expected = 'command arg-0'

    observed = basetest.GetCommandString('command arg-0')

    self.assertEqual(expected, observed)

  def testGetCommandString_unicodeStringArgument(self):
    expected = 'command arg-0'

    observed = basetest.GetCommandString(u'command arg-0')

    self.assertEqual(expected, observed)

  def testAssertRegexMatch_matches(self):
    self.assertRegexMatch('str', ['str'])

  def testAssertRegexMatch_matchesSubstring(self):
    self.assertRegexMatch('pre-str-post', ['str'])

  def testAssertRegexMatch_multipleRegexMatches(self):
    self.assertRegexMatch('str', ['rts', 'str'])

  def testAssertRegexMatch_emptyListFails(self):
    expected_re = re.compile(r'No regexes specified\.', re.MULTILINE)

    self.assertRaisesWithRegexpMatch(
        AssertionError,
        expected_re,
        self.assertRegexMatch,
        'str',
        regexes=[])

  def testAssertRegexMatch_badArguments(self):
    self.assertRaisesWithRegexpMatch(
        AssertionError,
        'regexes is a string; it needs to be a list of strings.',
        self.assertRegexMatch, '1.*2', '1 2')

  def testAssertCommandFailsStderr(self):
    self.assertCommandFails(
        ['/usr/bin/perl', '-e', 'die "FAIL";'],
        [r'(.|\n)*FAIL at -e line 1\.'])

  def testAssertCommandFailsWithListOfString(self):
    self.assertCommandFails(['false'], [''])

  def testAssertCommandFailsWithListOfUnicodeString(self):
    self.assertCommandFails([u'false'], [''])

  def testAssertCommandFailsWithUnicodeString(self):
    self.assertCommandFails(u'false', [''])

  def testAssertCommandSucceedsStderr(self):
    expected_re = re.compile(r'(.|\n)*FAIL at -e line 1\.', re.MULTILINE)

    self.assertRaisesWithRegexpMatch(
        AssertionError,
        expected_re,
        self.assertCommandSucceeds,
        ['/usr/bin/perl', '-e', 'die "FAIL";'])

  def testAssertCommandSucceedsWithMatchingRegexes(self):
    self.assertCommandSucceeds(['echo', 'SUCCESS'], regexes=['SUCCESS'])

  def testAssertCommandSucceedsWithNonMatchingRegexes(self):
    expected_re = re.compile(r'Running command', re.MULTILINE)

    self.assertRaisesWithRegexpMatch(
        AssertionError,
        expected_re,
        self.assertCommandSucceeds,
        ['echo', 'FAIL'],
        regexes=['SUCCESS'])

  def testAssertCommandSucceedsWithListOfString(self):
    self.assertCommandSucceeds(['true'])

  def testAssertCommandSucceedsWithListOfUnicodeString(self):
    self.assertCommandSucceeds([u'true'])

  def testAssertCommandSucceedsWithUnicodeString(self):
    self.assertCommandSucceeds(u'true')

  def testInequality(self):
    # Try ints
    self.assertGreater(2, 1)
    self.assertGreaterEqual(2, 1)
    self.assertGreaterEqual(1, 1)
    self.assertLess(1, 2)
    self.assertLessEqual(1, 2)
    self.assertLessEqual(1, 1)
    self.assertRaises(AssertionError, self.assertGreater, 1, 2)
    self.assertRaises(AssertionError, self.assertGreater, 1, 1)
    self.assertRaises(AssertionError, self.assertGreaterEqual, 1, 2)
    self.assertRaises(AssertionError, self.assertLess, 2, 1)
    self.assertRaises(AssertionError, self.assertLess, 1, 1)
    self.assertRaises(AssertionError, self.assertLessEqual, 2, 1)

    # Try Floats
    self.assertGreater(1.1, 1.0)
    self.assertGreaterEqual(1.1, 1.0)
    self.assertGreaterEqual(1.0, 1.0)
    self.assertLess(1.0, 1.1)
    self.assertLessEqual(1.0, 1.1)
    self.assertLessEqual(1.0, 1.0)
    self.assertRaises(AssertionError, self.assertGreater, 1.0, 1.1)
    self.assertRaises(AssertionError, self.assertGreater, 1.0, 1.0)
    self.assertRaises(AssertionError, self.assertGreaterEqual, 1.0, 1.1)
    self.assertRaises(AssertionError, self.assertLess, 1.1, 1.0)
    self.assertRaises(AssertionError, self.assertLess, 1.0, 1.0)
    self.assertRaises(AssertionError, self.assertLessEqual, 1.1, 1.0)

    # Try Strings
    self.assertGreater('bug', 'ant')
    self.assertGreaterEqual('bug', 'ant')
    self.assertGreaterEqual('ant', 'ant')
    self.assertLess('ant', 'bug')
    self.assertLessEqual('ant', 'bug')
    self.assertLessEqual('ant', 'ant')
    self.assertRaises(AssertionError, self.assertGreater, 'ant', 'bug')
    self.assertRaises(AssertionError, self.assertGreater, 'ant', 'ant')
    self.assertRaises(AssertionError, self.assertGreaterEqual, 'ant', 'bug')
    self.assertRaises(AssertionError, self.assertLess, 'bug', 'ant')
    self.assertRaises(AssertionError, self.assertLess, 'ant', 'ant')
    self.assertRaises(AssertionError, self.assertLessEqual, 'bug', 'ant')

    # Try Unicode
    self.assertGreater(u'bug', u'ant')
    self.assertGreaterEqual(u'bug', u'ant')
    self.assertGreaterEqual(u'ant', u'ant')
    self.assertLess(u'ant', u'bug')
    self.assertLessEqual(u'ant', u'bug')
    self.assertLessEqual(u'ant', u'ant')
    self.assertRaises(AssertionError, self.assertGreater, u'ant', u'bug')
    self.assertRaises(AssertionError, self.assertGreater, u'ant', u'ant')
    self.assertRaises(AssertionError, self.assertGreaterEqual, u'ant', u'bug')
    self.assertRaises(AssertionError, self.assertLess, u'bug', u'ant')
    self.assertRaises(AssertionError, self.assertLess, u'ant', u'ant')
    self.assertRaises(AssertionError, self.assertLessEqual, u'bug', u'ant')

    # Try Mixed String/Unicode
    self.assertGreater('bug', u'ant')
    self.assertGreater(u'bug', 'ant')
    self.assertGreaterEqual('bug', u'ant')
    self.assertGreaterEqual(u'bug', 'ant')
    self.assertGreaterEqual('ant', u'ant')
    self.assertGreaterEqual(u'ant', 'ant')
    self.assertLess('ant', u'bug')
    self.assertLess(u'ant', 'bug')
    self.assertLessEqual('ant', u'bug')
    self.assertLessEqual(u'ant', 'bug')
    self.assertLessEqual('ant', u'ant')
    self.assertLessEqual(u'ant', 'ant')
    self.assertRaises(AssertionError, self.assertGreater, 'ant', u'bug')
    self.assertRaises(AssertionError, self.assertGreater, u'ant', 'bug')
    self.assertRaises(AssertionError, self.assertGreater, 'ant', u'ant')
    self.assertRaises(AssertionError, self.assertGreater, u'ant', 'ant')
    self.assertRaises(AssertionError, self.assertGreaterEqual, 'ant', u'bug')
    self.assertRaises(AssertionError, self.assertGreaterEqual, u'ant', 'bug')
    self.assertRaises(AssertionError, self.assertLess, 'bug', u'ant')
    self.assertRaises(AssertionError, self.assertLess, u'bug', 'ant')
    self.assertRaises(AssertionError, self.assertLess, 'ant', u'ant')
    self.assertRaises(AssertionError, self.assertLess, u'ant', 'ant')
    self.assertRaises(AssertionError, self.assertLessEqual, 'bug', u'ant')
    self.assertRaises(AssertionError, self.assertLessEqual, u'bug', 'ant')

  def testAssertMultiLineEqual(self):
    sample_text = """\
http://www.python.org/doc/2.3/lib/module-unittest.html
test case
    A test case is the smallest unit of testing. [...]
"""
    revised_sample_text = """\
http://www.python.org/doc/2.4.1/lib/module-unittest.html
test case
    A test case is the smallest unit of testing. [...] You may provide your
    own implementation that does not subclass from TestCase, of course.
"""
    sample_text_error = """
- http://www.python.org/doc/2.3/lib/module-unittest.html
?                             ^
+ http://www.python.org/doc/2.4.1/lib/module-unittest.html
?                             ^^^
  test case
-     A test case is the smallest unit of testing. [...]
+     A test case is the smallest unit of testing. [...] You may provide your
?                                                       +++++++++++++++++++++
+     own implementation that does not subclass from TestCase, of course.
"""

    for type1 in (str, unicode):
      for type2 in (str, unicode):
        self.assertRaisesWithLiteralMatch(AssertionError, sample_text_error,
                                          self.assertMultiLineEqual,
                                          type1(sample_text),
                                          type2(revised_sample_text))

    self.assertRaises(AssertionError, self.assertMultiLineEqual, (1, 2), 'str')
    self.assertRaises(AssertionError, self.assertMultiLineEqual, 'str', (1, 2))

  def testAssertMultiLineEqualAddsNewlinesIfNeeded(self):
    self.assertRaisesWithLiteralMatch(
        AssertionError,
        '\n'
        '  line1\n'
        '- line2\n'
        '?     ^\n'
        '+ line3\n'
        '?     ^\n',
        self.assertMultiLineEqual,
        'line1\n'
        'line2',
        'line1\n'
        'line3')

  def testAssertMultiLineEqualShowsMissingNewlines(self):
    self.assertRaisesWithLiteralMatch(
        AssertionError,
        '\n'
        '  line1\n'
        '- line2\n'
        '?      -\n'
        '+ line2\n',
        self.assertMultiLineEqual,
        'line1\n'
        'line2\n',
        'line1\n'
        'line2')

  def testAssertMultiLineEqualShowsExtraNewlines(self):
    self.assertRaisesWithLiteralMatch(
        AssertionError,
        '\n'
        '  line1\n'
        '- line2\n'
        '+ line2\n'
        '?      +\n',
        self.assertMultiLineEqual,
        'line1\n'
        'line2',
        'line1\n'
        'line2\n')

  def testAssertIsNone(self):
    self.assertIsNone(None)
    self.assertRaises(AssertionError, self.assertIsNone, False)
    self.assertIsNotNone('Google')
    self.assertRaises(AssertionError, self.assertIsNotNone, None)
    self.assertRaises(AssertionError, self.assertIsNone, (1, 2))

  def testAssertIs(self):
    self.assertIs(object, object)
    self.assertRaises(AssertionError, self.assertIsNot, object, object)
    self.assertIsNot(True, False)
    self.assertRaises(AssertionError, self.assertIs, True, False)

  def testAssertBetween(self):
    self.assertBetween(3.14, 3.1, 3.141)
    self.assertBetween(4, 4, 1e10000)
    self.assertBetween(9.5, 9.4, 9.5)
    self.assertBetween(-1e10, -1e10000, 0)
    self.assertRaises(AssertionError, self.assertBetween, 9.4, 9.3, 9.3999)
    self.assertRaises(AssertionError, self.assertBetween, -1e10000, -1e10, 0)

  def testAssertRaisesWithPredicateMatch_noRaiseFails(self):
    self.assertRaisesWithRegexpMatch(
        AssertionError, '^Exception not raised$',
        self.assertRaisesWithPredicateMatch, Exception,
        lambda e: True,
        lambda: 1)  # don't raise

  def testAssertRaisesWithPredicateMatch_raisesWrongExceptionFails(self):
    def _RaiseValueError():
      raise ValueError

    self.assertRaises(
        ValueError,
        self.assertRaisesWithPredicateMatch,
        IOError, lambda e: True, _RaiseValueError)

  def testAssertRaisesWithPredicateMatch_predicateFails(self):
    def _RaiseValueError():
      raise ValueError
    self.assertRaisesWithRegexpMatch(
        AssertionError, ' does not match predicate ',
        self.assertRaisesWithPredicateMatch, ValueError,
        lambda e: False,
        _RaiseValueError)

  def testAssertRaisesWithPredicateMatch_predicatePasses(self):
    def _RaiseValueError():
      raise ValueError

    self.assertRaisesWithPredicateMatch (ValueError,
                                         lambda e: True,
                                         _RaiseValueError)

  def testAssertRaisesWithRegexpMatch(self):
    class ExceptionMock(Exception):
      pass

    def Stub():
      raise ExceptionMock('We expect')

    self.assertRaisesWithRegexpMatch(ExceptionMock, re.compile('expect$'), Stub)
    self.assertRaisesWithRegexpMatch(ExceptionMock, 'expect$', Stub)
    self.assertRaisesWithRegexpMatch(ExceptionMock, u'expect$', Stub)

  def testAssertNotRaisesWithRegexpMatch(self):
    self.assertRaisesWithRegexpMatch(
        AssertionError, '^Exception not raised$',
        self.assertRaisesWithRegexpMatch, Exception, re.compile('x'),
        lambda: None)
    self.assertRaisesWithRegexpMatch(
        AssertionError, '^Exception not raised$',
        self.assertRaisesWithRegexpMatch, Exception, 'x', lambda: None)
    self.assertRaisesWithRegexpMatch(
        AssertionError, '^Exception not raised$',
        self.assertRaisesWithRegexpMatch, Exception, u'x', lambda: None)

  def testAssertRaisesWithRegexpMismatch(self):
    def Stub():
      raise Exception('Unexpected')

    self.assertRaisesWithRegexpMatch(
        AssertionError, r'"\^Expected\$" does not match "Unexpected"',
        self.assertRaisesWithRegexpMatch, Exception, r'^Expected$', Stub)
    self.assertRaisesWithRegexpMatch(
        AssertionError, r'"\^Expected\$" does not match "Unexpected"',
        self.assertRaisesWithRegexpMatch, Exception, r'^Expected$', Stub)

  def testAssertContainsInOrder(self):
    # Valids
    self.assertContainsInOrder(
        ['fox', 'dog'], 'The quick brown fox jumped over the lazy dog.')
    self.assertContainsInOrder(
        ['quick', 'fox', 'dog'],
        'The quick brown fox jumped over the lazy dog.')
    self.assertContainsInOrder(
        ['The', 'fox', 'dog.'], 'The quick brown fox jumped over the lazy dog.')
    self.assertContainsInOrder(
        ['fox'], 'The quick brown fox jumped over the lazy dog.')
    self.assertContainsInOrder(
        'fox', 'The quick brown fox jumped over the lazy dog.')
    self.assertContainsInOrder(
        ['fox', 'dog'], 'fox dog fox')
    self.assertContainsInOrder(
        [], 'The quick brown fox jumped over the lazy dog.')
    self.assertContainsInOrder(
        [], '')

    # Invalids
    self.assertRaises(
        AssertionError, self.assertContainsInOrder,
        ['dog', 'fox'], 'The quick brown fox jumped over the lazy dog')
    self.assertRaises(
        AssertionError, self.assertContainsInOrder,
        ['The', 'dog', 'fox'], 'The quick brown fox jumped over the lazy dog')
    self.assertRaises(
        AssertionError, self.assertContainsInOrder, ['dog'], '')

  def testAssertTotallyOrdered(self):
    # Valid.
    self.assertTotallyOrdered()
    self.assertTotallyOrdered([1])
    self.assertTotallyOrdered([1], [2])
    self.assertTotallyOrdered([None], [1], [2])
    self.assertTotallyOrdered([1, 1, 1])
    self.assertTotallyOrdered([1, 1, 1], ['a string'])
    self.assertTotallyOrdered([(1, 1)], [(1, 2)], [(2, 1)])

    # From the docstring.
    class A(object):
      def __init__(self, x, y):
        self.x = x
        self.y = y

      def __hash__(self):
        return hash(self.x)

      def __repr__(self):
        return 'A(%r, %r)' % (self.x, self.y)

      def __eq__(self, other):
        try:
          return self.x == other.x
        except AttributeError:
          return NotImplemented

      def __ne__(self, other):
        try:
          return self.x != other.x
        except AttributeError:
          return NotImplemented

      def __lt__(self, other):
        try:
          return self.x < other.x
        except AttributeError:
          return NotImplemented

      def __le__(self, other):
        try:
          return self.x <= other.x
        except AttributeError:
          return NotImplemented

      def __gt__(self, other):
        try:
          return self.x > other.x
        except AttributeError:
          return NotImplemented

      def __ge__(self, other):
        try:
          return self.x >= other.x
        except AttributeError:
          return NotImplemented

    self.assertTotallyOrdered(
        [None],  # None should come before everything else.
        [1],     # Integers sort earlier.
        [A(1, 'a')],
        [A(2, 'b')],  # 2 is after 1.
        [A(3, 'c'), A(3, 'd')],  # The second argument is irrelevant.
        [A(4, 'z')],
        ['foo'])  # Strings sort last.

    # Invalid.
    self.assertRaises(AssertionError, self.assertTotallyOrdered, [2], [1])
    self.assertRaises(AssertionError, self.assertTotallyOrdered, [2], [1], [3])
    self.assertRaises(AssertionError, self.assertTotallyOrdered, [1, 2])

  def testShortDescriptionWithoutDocstring(self):
    self.assertEquals(
        self.shortDescription(),
        ('testShortDescriptionWithoutDocstring '
         '(%s.GoogleTestBaseUnitTest)' % __name__))

  def testShortDescriptionWithOneLineDocstring(self):
    """Tests shortDescription() for a method with a docstring."""
    self.assertEquals(
        self.shortDescription(),
        ('testShortDescriptionWithOneLineDocstring '
         '(%s.GoogleTestBaseUnitTest)\n'
         'Tests shortDescription() for a method with a docstring.' % __name__))

  def testShortDescriptionWithMultiLineDocstring(self):
    """Tests shortDescription() for a method with a longer docstring.

    This method ensures that only the first line of a docstring is
    returned used in the short description, no matter how long the
    whole thing is.
    """
    self.assertEquals(
        self.shortDescription(),
        ('testShortDescriptionWithMultiLineDocstring '
         '(%s.GoogleTestBaseUnitTest)\n'
         'Tests shortDescription() for a method with a longer docstring.'
         % __name__))

  def testRecordedProperties(self):
    """Tests that a test can record a property and then retrieve it."""
    self.recordProperty('test_property', 'test_value')
    self.assertEquals(self.getRecordedProperties(),
                      {'test_property': 'test_value'})


class GetCommandStderrTestCase(basetest.TestCase):

  def setUp(self):
    self.original_environ = os.environ.copy()

  def tearDown(self):
    os.environ = self.original_environ

  def testReturnStatus(self):
    expected = 255

    observed = (
        basetest.GetCommandStderr(
            ['/usr/bin/perl', '-e', 'die "FAIL";'],
            None)[0])

    self.assertEqual(expected, observed)

  # TODO(dborowitz): Tests for more functionality that do not deal with
  # PYTHON_RUNFILES.


class EqualityAssertionTest(basetest.TestCase):
  """This test verifies that basetest.failIfEqual actually tests __ne__.

  If a user class implements __eq__, unittest.failUnlessEqual will call it
  via first == second.   However, failIfEqual also calls
  first == second.   This means that while the caller may believe
  their __ne__ method is being tested, it is not.
  """

  class NeverEqual(object):
    """Objects of this class behave like NaNs."""

    def __eq__(self, unused_other):
      return False

    def __ne__(self, unused_other):
      return False

  class AllSame(object):
    """All objects of this class compare as equal."""

    def __eq__(self, unused_other):
      return True

    def __ne__(self, unused_other):
      return False

  class EqualityTestsWithEq(object):
    """Performs all equality and inequality tests with __eq__."""

    def __init__(self, value):
      self._value = value

    def __eq__(self, other):
      return self._value == other._value

    def __ne__(self, other):
      return not self.__eq__(other)

  class EqualityTestsWithNe(object):
    """Performs all equality and inequality tests with __ne__."""

    def __init__(self, value):
      self._value = value

    def __eq__(self, other):
      return not self.__ne__(other)

    def __ne__(self, other):
      return self._value != other._value

  class EqualityTestsWithCmp(object):

    def __init__(self, value):
      self._value = value

    def __cmp__(self, other):
      return cmp(self._value, other._value)

  def testAllComparisonsFail(self):
    i1 = self.NeverEqual()
    i2 = self.NeverEqual()
    self.assertFalse(i1 == i2)
    self.assertFalse(i1 != i2)

    # Compare two distinct objects
    self.assertFalse(i1 is i2)
    self.assertRaises(AssertionError, self.assertEqual, i1, i2)
    self.assertRaises(AssertionError, self.assertEquals, i1, i2)
    self.assertRaises(AssertionError, self.failUnlessEqual, i1, i2)
    self.assertRaises(AssertionError, self.assertNotEqual, i1, i2)
    self.assertRaises(AssertionError, self.assertNotEquals, i1, i2)
    self.assertRaises(AssertionError, self.failIfEqual, i1, i2)
    # A NeverEqual object should not compare equal to itself either.
    i2 = i1
    self.assertTrue(i1 is i2)
    self.assertFalse(i1 == i2)
    self.assertFalse(i1 != i2)
    self.assertRaises(AssertionError, self.assertEqual, i1, i2)
    self.assertRaises(AssertionError, self.assertEquals, i1, i2)
    self.assertRaises(AssertionError, self.failUnlessEqual, i1, i2)
    self.assertRaises(AssertionError, self.assertNotEqual, i1, i2)
    self.assertRaises(AssertionError, self.assertNotEquals, i1, i2)
    self.assertRaises(AssertionError, self.failIfEqual, i1, i2)

  def testAllComparisonsSucceed(self):
    a = self.AllSame()
    b = self.AllSame()
    self.assertFalse(a is b)
    self.assertTrue(a == b)
    self.assertFalse(a != b)
    self.assertEqual(a, b)
    self.assertEquals(a, b)
    self.failUnlessEqual(a, b)
    self.assertRaises(AssertionError, self.assertNotEqual, a, b)
    self.assertRaises(AssertionError, self.assertNotEquals, a, b)
    self.assertRaises(AssertionError, self.failIfEqual, a, b)

  def _PerformAppleAppleOrangeChecks(self, same_a, same_b, different):
    """Perform consistency checks with two apples and an orange.

    The two apples should always compare as being the same (and inequality
    checks should fail).  The orange should always compare as being different
    to each of the apples.

    Args:
      same_a: the first apple
      same_b: the second apple
      different: the orange
    """
    self.assertTrue(same_a == same_b)
    self.assertFalse(same_a != same_b)
    self.assertEqual(same_a, same_b)
    self.assertEquals(same_a, same_b)
    self.failUnlessEqual(same_a, same_b)
    self.assertEqual(0, cmp(same_a, same_b))

    self.assertFalse(same_a == different)
    self.assertTrue(same_a != different)
    self.assertNotEqual(same_a, different)
    self.assertNotEquals(same_a, different)
    self.failIfEqual(same_a, different)
    self.assertNotEqual(0, cmp(same_a, different))

    self.assertFalse(same_b == different)
    self.assertTrue(same_b != different)
    self.assertNotEqual(same_b, different)
    self.assertNotEquals(same_b, different)
    self.failIfEqual(same_b, different)
    self.assertNotEqual(0, cmp(same_b, different))

  def testComparisonWithEq(self):
    same_a = self.EqualityTestsWithEq(42)
    same_b = self.EqualityTestsWithEq(42)
    different = self.EqualityTestsWithEq(1769)
    self._PerformAppleAppleOrangeChecks(same_a, same_b, different)

  def testComparisonWithNe(self):
    same_a = self.EqualityTestsWithNe(42)
    same_b = self.EqualityTestsWithNe(42)
    different = self.EqualityTestsWithNe(1769)
    self._PerformAppleAppleOrangeChecks(same_a, same_b, different)

  def testComparisonWithCmp(self):
    same_a = self.EqualityTestsWithCmp(42)
    same_b = self.EqualityTestsWithCmp(42)
    different = self.EqualityTestsWithCmp(1769)
    self._PerformAppleAppleOrangeChecks(same_a, same_b, different)


class GoogleTestBasePy24UnitTest(basetest.TestCase):

  def RunTestCaseTests(self, test_case_class):
    test_loader = test_case_class._test_loader
    test_loader.loadTestsFromTestCase(
        test_case_class).run(unittest.TestResult())

  def testSetUpCalledForEachTestMethod(self):
    self.RunTestCaseTests(SetUpSpy)

    self.assertEquals(2, SetUpSpy.set_up_counter)

  def testSetUpTestCaseCalledExactlyOnce(self):
    self.RunTestCaseTests(SetUpTestCaseSpy)

    self.assertEquals(1, SetUpTestCaseSpy.set_up_test_case_counter)

  def testTearDownCalledForEachTestMethod(self):
    self.RunTestCaseTests(TearDownSpy)

    self.assertEquals(2, TearDownSpy.tear_down_counter)

  def testTearDownTestCaseCalledExactlyOnce(self):
    self.RunTestCaseTests(TearDownTestCaseSpy)

    self.assertEquals(1, TearDownTestCaseSpy.tear_down_test_case_counter)

  def testDefaultSetUpTestCaseExists(self):
    self.assertTrue(
        hasattr(OnlyBeforeAfterTestCaseMetaDefinedSpy, 'setUpTestCase'))

  def testDefaultTearDownTestCaseExists(self):
    self.assertTrue(
        hasattr(OnlyBeforeAfterTestCaseMetaDefinedSpy, 'tearDownTestCase'))

  def testBeforeAfterWithInheritanceAndOverridesA(self):
    """Test that things work when there's subclassing and overrides."""
    InheritanceSpyBaseClass.ClearLog()
    self.RunTestCaseTests(InheritanceSpySubClassA)

    expected_calls = [
        'sub setUpTestCase',
        'base setUp',
        'base StubTest0',
        'sub tearDown',
        'base setUp',
        'sub StubTest1',
        'sub tearDown',
        'base tearDownTestCase']

    self.assertSequenceEqual(expected_calls,
                             InheritanceSpyBaseClass.calls_made)

  def testBeforeAfterWithInheritanceAndOverridesB(self):
    """Complementary to the other test, test39A."""
    InheritanceSpyBaseClass.ClearLog()
    self.RunTestCaseTests(InheritanceSpySubClassB)

    expected_calls = [
        'base setUpTestCase',
        'sub setUp',
        'sub StubTest0',
        'base tearDown',
        'sub setUp',
        'sub StubTest1',
        'base tearDown',
        'sub setUp',
        'sub StubTest2',
        'base tearDown',
        'sub tearDownTestCase']

    self.assertSequenceEqual(expected_calls,
                             InheritanceSpyBaseClass.calls_made)

  def testVerifyTearDownOrder(self):
    """Verify that tearDownTestCase gets called at the correct time."""
    TearDownOrderWatcherBaseClass.ClearLog()
    self.RunTestCaseTests(TearDownOrderWatcherSubClass)

    expected_calls = [
        'TearDownOrderWatcherBaseClass.setUpTestCase',
        'TearDownOrderWatcherSubClass.setUp Start',
        'TearDownOrderWatcherBaseClass.setUp',
        'TearDownOrderWatcherSubClass.setUp Finish',
        'testAAAA',
        'TearDownOrderWatcherSubClass.tearDown Start',
        'TearDownOrderWatcherBaseClass.tearDown',
        'TearDownOrderWatcherSubClass.tearDown Finish',
        'TearDownOrderWatcherBaseClass.tearDownTestCase']

    self.assertSequenceEqual(expected_calls,
                             TearDownOrderWatcherBaseClass.calls_made)


class StubPrefixedTestMethodsTestCase(basetest.TestCase):

  _test_loader = unittest.TestLoader()
  _test_loader.testMethodPrefix = 'StubTest'

  def StubTest0(self):
    pass

  def StubTest1(self):
    pass


class SetUpSpy(StubPrefixedTestMethodsTestCase):
  __metaclass__ = basetest.BeforeAfterTestCaseMeta
  set_up_counter = 0

  def setUp(self):
    StubPrefixedTestMethodsTestCase.setUp(self)
    SetUpSpy.set_up_counter += 1


class SetUpTestCaseSpy(StubPrefixedTestMethodsTestCase):

  __metaclass__ = basetest.BeforeAfterTestCaseMeta

  set_up_test_case_counter = 0

  def setUpTestCase(self):
    StubPrefixedTestMethodsTestCase.setUpTestCase(self)
    SetUpTestCaseSpy.set_up_test_case_counter += 1


class TearDownSpy(StubPrefixedTestMethodsTestCase):

  __metaclass__ = basetest.BeforeAfterTestCaseMeta

  tear_down_counter = 0

  def tearDown(self):
    TearDownSpy.tear_down_counter += 1
    StubPrefixedTestMethodsTestCase.tearDown(self)


class TearDownTestCaseSpy(StubPrefixedTestMethodsTestCase):

  __metaclass__ = basetest.BeforeAfterTestCaseMeta

  tear_down_test_case_counter = 0

  def tearDownTestCase(self):
    TearDownTestCaseSpy.tear_down_test_case_counter += 1
    StubPrefixedTestMethodsTestCase.tearDownTestCase(self)


class OnlyBeforeAfterTestCaseMetaDefinedSpy(basetest.TestCase):

  __metaclass__ = basetest.BeforeAfterTestCaseMeta


# Here we define 3 classes: a base class and two subclasses inheriting from it.
# The base class has implementations for all four setUp / tearDown methods, and
# the two subclasses override complementary subsets of them: one does
# setUpTestCase and tearDown, the other setUp and tearDownTestCase.  This way we
# can check that overriding each method works, and that they don't have to be
# overriden in matching pairs.

# We use an even number of test methods in one test (2 in A) and an odd number
# in the other (3 in B) intentionally.  These failed in different ways with the
# old code.  With an even number of test methods, the old code calls
# tearDownTestCase early; with an odd number of test methods tearDownTestCase
# would not be called.  The older implementation calls tearDownTestCase when its
# counter of tests remaining reached zero.  When double counting, if there were
# 2 test methods, it'd hit 0 after executing only 1 of them.  If there were 3,
# it would go from 3 to 1 to -1, skipping 0 entirely.


class InheritanceSpyBaseClass(basetest.TestCase):

  __metaclass__ = basetest.BeforeAfterTestCaseMeta

  calls_made = []

  @staticmethod
  def Log(call):
    InheritanceSpyBaseClass.calls_made.append(call)

  @staticmethod
  def ClearLog():
    InheritanceSpyBaseClass.calls_made = []

  def setUpTestCase(self):
    self.Log('base setUpTestCase')

  def tearDownTestCase(self):
    self.Log('base tearDownTestCase')

  def setUp(self):
    self.Log('base setUp')

  def tearDown(self):
    self.Log('base tearDown')

  def StubTest0(self):
    self.Log('base StubTest0')


class InheritanceSpySubClassA(InheritanceSpyBaseClass):
  _test_loader = unittest.TestLoader()
  _test_loader.testMethodPrefix = 'StubTest'

  def StubTest1(self):
    self.Log('sub StubTest1')

  def setUpTestCase(self):
    self.Log('sub setUpTestCase')

  def tearDown(self):
    self.Log('sub tearDown')


class InheritanceSpySubClassB(InheritanceSpyBaseClass):
  _test_loader = unittest.TestLoader()
  _test_loader.testMethodPrefix = 'StubTest'

  # Intentionally mask StubTest0 from the base class
  def StubTest0(self):
    self.Log('sub StubTest0')

  def StubTest1(self):
    self.Log('sub StubTest1')

  def StubTest2(self):
    self.Log('sub StubTest2')

  def setUp(self):
    self.Log('sub setUp')

  def tearDownTestCase(self):
    self.Log('sub tearDownTestCase')


# We define another pair of base/subclass here to verify that tearDown
# and tearDownTestCase always happen in the correct order.
class TearDownOrderWatcherBaseClass(basetest.TestCase):
  __metaclass__ = basetest.BeforeAfterTestCaseMeta

  calls_made = []

  @staticmethod
  def Log(call):
    TearDownOrderWatcherBaseClass.calls_made.append(call)

  @staticmethod
  def ClearLog():
    TearDownOrderWatcherBaseClass.calls_made = []

  def __init__(self, *args, **kwds):
    super(TearDownOrderWatcherBaseClass, self).__init__(*args, **kwds)

  def setUpTestCase(self):
    self.Log('TearDownOrderWatcherBaseClass.setUpTestCase')

  def tearDownTestCase(self):
    self.Log('TearDownOrderWatcherBaseClass.tearDownTestCase')

  def setUp(self):
    self.Log('TearDownOrderWatcherBaseClass.setUp')

  def tearDown(self):
    self.Log('TearDownOrderWatcherBaseClass.tearDown')


class TearDownOrderWatcherSubClass(TearDownOrderWatcherBaseClass):
  def setUp(self):
    self.Log('TearDownOrderWatcherSubClass.setUp Start')
    super(TearDownOrderWatcherSubClass, self).setUp()
    self.Log('TearDownOrderWatcherSubClass.setUp Finish')

  def tearDown(self):
    self.Log('TearDownOrderWatcherSubClass.tearDown Start')
    super(TearDownOrderWatcherSubClass, self).tearDown()
    self.Log('TearDownOrderWatcherSubClass.tearDown Finish')

  def testAAAA(self):
    self.Log('testAAAA')
    self.assertTrue(True)


# We define a multiply inheriting metaclass and an instance class to verify that
# multiple inheritance for metaclasses.
class OtherMetaClass(type):
  def __init__(cls, name, bases, dict):
    super(OtherMetaClass, cls).__init__(name, bases, dict)
    cls.other_meta_called = True


class MultipleMetaBeforeAfter(basetest.BeforeAfterTestCaseMeta, OtherMetaClass):
  """Allow classes to support BeforeAfterTestCase and another metaclass.

  Order matters here since we want to make sure BeforeAfterTestCaseMeta passes
  through correctly to the other metaclass.
  """


class MultipleMetaInstanceClass(basetest.TestCase):
  __metaclass__ = MultipleMetaBeforeAfter

  def testOtherMetaInitCalled(self):
    self.assertTrue(hasattr(MultipleMetaInstanceClass, 'other_meta_called'))


class AssertSequenceStartsWithTest(basetest.TestCase):

  def setUp(self):
    self.a = [5, 'foo', {'c': 'd'}, None]

  def testEmptySequenceStartsWithEmptyPrefix(self):
    self.assertSequenceStartsWith([], ())

  def testSequencePrefixIsAnEmptyList(self):
    self.assertSequenceStartsWith([[]], ([], 'foo'))

  def testRaiseIfEmptyPrefixWithNonEmptyWhole(self):
    self.assertRaisesWithRegexpMatch(
        AssertionError,
        'Prefix length is 0 but whole length is %d: %s' % (
            len(self.a), '\[5, \'foo\', \{\'c\': \'d\'\}, None\]'),
        self.assertSequenceStartsWith, [], self.a)

  def testSingleElementPrefix(self):
    self.assertSequenceStartsWith([5], self.a)

  def testTwoElementPrefix(self):
    self.assertSequenceStartsWith((5, 'foo'), self.a)

  def testPrefixIsFullSequence(self):
    self.assertSequenceStartsWith([5, 'foo', {'c': 'd'}, None], self.a)

  def testStringPrefix(self):
    self.assertSequenceStartsWith('abc', 'abc123')

  def testConvertNonSequencePrefixToSequenceAndTryAgain(self):
    self.assertSequenceStartsWith(5, self.a)

  def testWholeNotASequence(self):
    msg = ('For whole: len\(5\) is not supported, it appears to be type: '
           '<type \'int\'>')
    self.assertRaisesWithRegexpMatch(AssertionError, msg,
                                     self.assertSequenceStartsWith, self.a, 5)

  def testRaiseIfSequenceDoesNotStartWithPrefix(self):
    msg = ('prefix: \[\'foo\', \{\'c\': \'d\'\}\] not found at start of whole: '
           '\[5, \'foo\', \{\'c\': \'d\'\}, None\].')
    self.assertRaisesWithRegexpMatch(
        AssertionError, msg, self.assertSequenceStartsWith, ['foo', {'c': 'd'}],
        self.a)

  def testRaiseIfTypesArNotSupported(self):
    self.assertRaisesWithRegexpMatch(
        TypeError, 'unhashable type', self.assertSequenceStartsWith,
        {'a': 1, 2: 'b'}, {'a': 1, 2: 'b', 'c': '3'})


class InitNotNecessaryForAssertsTest(basetest.TestCase):
  '''TestCase assertions should work even if __init__ wasn't correctly
  called.

  This is a hack, see comment in
  basetest.TestCase._getAssertEqualityFunc. We know that not calling
  __init__ of a superclass is a bad thing, but people keep doing them,
  and this (even if a little bit dirty) saves them from shooting
  themselves in the foot.
  '''
  def testSubclass(self):
    class Subclass(basetest.TestCase):
      def __init__(self):
        pass

    Subclass().assertEquals({}, {})

  def testMultipleInheritance(self):

    class Foo(object):
      def __init__(self, *args, **kwargs):
        pass

    class Subclass(Foo, basetest.TestCase):
      pass

    Subclass().assertEquals({}, {})
if __name__ == '__main__':
  basetest.main()
