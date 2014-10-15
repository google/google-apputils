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
import string
import sys
import unittest

import gflags as flags
from google.apputils import basetest

PY_VERSION_2 = sys.version_info[0] == 2

FLAGS = flags.FLAGS

flags.DEFINE_integer('testid', 0, 'Which test to run')


_OUTPUT_CAPTURING_CASES = [
    (basetest.CaptureTestStdout, basetest.DiffTestStdout, sys.stdout),
    (basetest.CaptureTestStderr, basetest.DiffTestStderr, sys.stderr),
]


class CaptureTestStdoutStderrTest(basetest.TestCase):

  def setUp(self):
    self.expected_filepath = os.path.join(FLAGS.test_tmpdir, 'expected_output')

  def testStdoutCapturedSuccessfully(self):
    for capture_output_fn, diff_output_fn, ostream in _OUTPUT_CAPTURING_CASES:
      capture_output_fn()
      ostream.write('This gets captured\n')
      with open(self.expected_filepath, 'wb') as expected_file:
        expected_file.write(b'This gets captured\n')
      diff_output_fn(self.expected_filepath)  # should do nothing

  def testRaisesWhenCapturedStdoutDifferentThanExpected(self):
    for capture_output_fn, diff_output_fn, ostream in _OUTPUT_CAPTURING_CASES:
      capture_output_fn()
      ostream.write('Correct captured.out\n')
      with open(self.expected_filepath, 'wb') as expected_file:
        expected_file.write(b'Incorrect captured.out\n')
      self.assertRaises(basetest.OutputDifferedError,
                        diff_output_fn, self.expected_filepath)

  def testStdoutNoLongerCapturedAfterDiffTest(self):
    for capture_output_fn, diff_output_fn, ostream in _OUTPUT_CAPTURING_CASES:
      with open(self.expected_filepath, 'wb') as expected_file:
        expected_file.write(b'This goes to captured.out\n')
      capture_output_fn()
      ostream.write('This goes to captured.out\n')
      diff_output_fn(self.expected_filepath)  # should do nothing
      ostream.write('This goes to stdout screen\n')
      capture_output_fn()
      ostream.write('This goes to captured.out\n')
      diff_output_fn(self.expected_filepath)  # should do nothing

  def testCapturingTestStdoutReturnsContextManager(self):
    for capture_output_fn, _, ostream in _OUTPUT_CAPTURING_CASES:
      with open(self.expected_filepath, 'wb') as expected_file:
        expected_file.write(b'This goes to captured.out\n')
      ostream.write('This goes to stdout screen\n')
      with capture_output_fn(
          expected_output_filepath=self.expected_filepath):
        ostream.write('This goes to captured.out\n')


class GoogleTestBaseUnitTest(basetest.TestCase):

  def setUp(self):
    self._orig_test_diff = os.environ.pop('TEST_DIFF', None)
    self.data1_file = os.path.join(FLAGS.test_tmpdir, 'provided_1.dat')
    self.data2_file = os.path.join(FLAGS.test_tmpdir, 'provided_2.dat')

  def tearDown(self):
    if self._orig_test_diff is not None:
      os.environ['TEST_DIFF'] = self._orig_test_diff

  def test_Diff_SameData(self):
    """Tests for the internal _Diff method."""
    basetest._WriteTestData('a\nb\n', self.data1_file)
    basetest._WriteTestData('a\nb\n', self.data2_file)
    # This must not raise an exception:
    basetest._Diff(self.data1_file, self.data2_file)

  @unittest.skipIf(not os.path.exists('/usr/bin/diff'),
                   'requires /usr/bin/diff')
  def test_Diff_SameData_ExternalDiff(self):
    """Test the internal _Diff method when TEST_DIFF is in the env."""
    os.environ['TEST_DIFF'] = '/usr/bin/diff'
    basetest._WriteTestData('b\n', self.data1_file)
    basetest._WriteTestData('b\n', self.data2_file)
    # This must not raise an exception:
    basetest._Diff(self.data1_file, self.data2_file)

  @unittest.skipIf(not os.path.exists('/usr/bin/diff'),
                   'requires /usr/bin/diff')
  def test_Diff_MissingFile_ExternalDiff(self):
    """Test the internal _Diff method on TEST_DIFF error."""
    os.environ['TEST_DIFF'] = '/usr/bin/diff'
    basetest._WriteTestData('a\n', self.data1_file)
    if os.path.exists(self.data2_file):
      os.unlink(self.data2_file)  # Be 100% sure this does not exist.
    # This depends on /usr/bin/diff returning an exit code greater than 1
    # when an input file is missing.  It has had this behavior forever.
    with self.assertRaises(basetest.DiffFailureError) as error_context:
      basetest._Diff(self.data1_file, self.data2_file)

  def test_Diff_MissingExternalDiff(self):
    """Test the internal _Diff when TEST_DIFF program is non-existant."""
    os.environ['TEST_DIFF'] = self.data1_file
    if os.path.exists(self.data1_file):
      os.unlink(self.data1_file)  # Be 100% sure this does not exist
    with self.assertRaises(basetest.DiffFailureError) as error_context:
      basetest._Diff(self.data2_file, self.data2_file)

  def test_Diff_Exception(self):
    """Test that _Diff includes the delta in the error msg."""
    basetest._WriteTestData(b'01: text A\n02: text B\n03: C', self.data1_file)
    basetest._WriteTestData(b'01: text A\n02: zzzzzz\n03: C', self.data2_file)

    with self.assertRaises(basetest.OutputDifferedError) as error_context:
      basetest._Diff(self.data1_file, self.data2_file)

    # Check that both filenames and some semblance of a unified diff
    # are present in the exception error message.
    diff_error_message = str(error_context.exception)
    self.assertIn('provided_1', diff_error_message)
    self.assertIn('provided_2', diff_error_message)
    self.assertIn('@@', diff_error_message)
    self.assertIn('02: text B', diff_error_message)

  @unittest.skipIf(not os.path.exists('/usr/bin/diff'),
                   'requires /usr/bin/diff')
  def test_Diff_Exception_ExternalDiff(self):
    """Test that _Diff executes TEST_DIFF when supplied and there are diffs."""
    os.environ['TEST_DIFF'] = '/usr/bin/diff'
    basetest._WriteTestData(b'01: text A\n02: text B\n03: C', self.data1_file)
    basetest._WriteTestData(b'01: text A\n02: zzzzzz\n03: C', self.data2_file)

    with self.assertRaises(basetest.OutputDifferedError) as error_context:
      basetest._Diff(self.data1_file, self.data2_file)

    # Check that both filenames and the TEST_DIFF command
    # are present in the exception error message.
    diff_error_message = str(error_context.exception)
    self.assertIn('/usr/bin/diff', diff_error_message)
    self.assertIn('provided_1', diff_error_message)
    self.assertIn('provided_2', diff_error_message)

  def testDiffTestStrings(self):
    basetest.DiffTestStrings('a', 'a')
    with self.assertRaises(basetest.OutputDifferedError):
      basetest.DiffTestStrings(
          '-2: a message\n-2: another message\n',
          '-2: a message\n-2: another message \n')
    self.assertRaises(basetest.DiffFailureError, basetest.DiffTestStringFile,
                      'a message', 'txt.a message not existant file here')
    self.assertRaises(basetest.OutputDifferedError, basetest.DiffTestStringFile,
                      'message', os.devnull)


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

  @basetest.unittest.expectedFailure
  def testExpectedFailure(self):
    if FLAGS.testid == 7:
      self.assertEqual(1, 1)  # expected failure, got success
    else:
      self.assertEqual(1, 2)  # the expected failure

  @basetest.unittest.expectedFailure
  def testDifferentExpectedFailure(self):
    if FLAGS.testid == 8:
      self.assertEqual(1, 1)  # expected failure, got success
    else:
      self.assertEqual(1, 2)  # the expected failure

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
    if PY_VERSION_2:
      # dict's are no longer valid for < comparison in Python 3 making them
      # unsortable (yay, sanity!).  But we need to preserve this old behavior
      # when running under Python 2.
      self.assertSameElements([{'a': 1}, {'b': 2}], [{'b': 2}, {'a': 1}])
    self.assertRaises(AssertionError, self.assertSameElements, [[1]], [[2]])

  def testAssertItemsEqualHotfix(self):
    """Confirm that http://bugs.python.org/issue14832 - b/10038517 is gone."""
    for assert_items_method in (self.assertItemsEqual, self.assertCountEqual):
      with self.assertRaises(self.failureException) as error_context:
        assert_items_method([4], [2])
      error_message = str(error_context.exception)
      # Confirm that the bug is either no longer present in Python or that our
      # assertItemsEqual patching version of the method in basetest.TestCase
      # doesn't get used.
      self.assertIn('First has 1, Second has 0:  4', error_message)
      self.assertIn('First has 0, Second has 1:  2', error_message)

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
      # Ensure we use equality as the sole measure of elements, not type, since
      # that is consistent with dict equality.
      self.assertDictEqual({1: 1.0, 2: 2}, {1: 1, 2: 3})
    except AssertionError, e:
      self.assertMultiLineEqual('{1: 1.0, 2: 2} != {1: 1, 2: 3}\n'
                                'repr() of differing entries:\n2: 2 != 3\n',
                                str(e))

    try:
      self.assertDictEqual({}, {'x': 1})
    except AssertionError, e:
      self.assertMultiLineEqual("{} != {'x': 1}\n"
                                "Unexpected, but present entries:\n'x': 1\n",
                                str(e))
    else:
      self.fail('Expecting AssertionError')

    try:
      self.assertDictEqual({}, {'x': 1}, 'a message')
    except AssertionError, e:
      self.assertIn('a message', str(e))
    else:
      self.fail('Expecting AssertionError')

    expected = {'a': 1, 'b': 2, 'c': 3}
    seen = {'a': 2, 'c': 3, 'd': 4}
    try:
      self.assertDictEqual(expected, seen)
    except AssertionError, e:
      self.assertMultiLineEqual("""\
{'a': 1, 'b': 2, 'c': 3} != {'a': 2, 'c': 3, 'd': 4}
Unexpected, but present entries:
'd': 4

repr() of differing entries:
'a': 1 != 2

Missing entries:
'b': 2
""", str(e))
    else:
      self.fail('Expecting AssertionError')

    self.assertRaises(AssertionError, self.assertDictEqual, (1, 2), {})
    self.assertRaises(AssertionError, self.assertDictEqual, {}, (1, 2))

    # Ensure deterministic output of keys in dictionaries whose sort order
    # doesn't match the lexical ordering of repr -- this is most Python objects,
    # which are keyed by memory address.
    class Obj(object):

      def __init__(self, name):
        self.name = name

      def __repr__(self):
        return self.name

    try:
      self.assertDictEqual(
          {'a': Obj('A'), Obj('b'): Obj('B'), Obj('c'): Obj('C')},
          {'a': Obj('A'), Obj('d'): Obj('D'), Obj('e'): Obj('E')})
    except AssertionError, e:
      # Do as best we can not to be misleading when objects have the same repr
      # but aren't equal.
      err_str = str(e)
      self.assertStartsWith(err_str,
                            "{'a': A, b: B, c: C} != {'a': A, d: D, e: E}\n")
      self.assertRegexpMatches(err_str,
                               r'(?ms).*^Unexpected, but present entries:\s+'
                               r'^(d: D$\s+^e: E|e: E$\s+^d: D)$')
      self.assertRegexpMatches(err_str,
                               r'(?ms).*^repr\(\) of differing entries:\s+'
                               r'^.a.: A != A$', err_str)
      self.assertRegexpMatches(err_str,
                               r'(?ms).*^Missing entries:\s+'
                               r'^(b: B$\s+^c: C|c: C$\s+^b: B)$')
    else:
      self.fail('Expecting AssertionError')

    # Confirm that safe_repr, not repr, is being used.
    class RaisesOnRepr(object):

      def __repr__(self):
        return 1/0  # Intentionally broken __repr__ implementation.

    try:
      self.assertDictEqual(
          {RaisesOnRepr(): RaisesOnRepr()},
          {RaisesOnRepr(): RaisesOnRepr()}
          )
      self.fail('Expected dicts not to match')
    except AssertionError as e:
      # Depending on the testing environment, the object may get a __main__
      # prefix or a basetest_test prefix, so strip that for comparison.
      error_msg = re.sub(
          r'( at 0x[^>]+)|__main__\.|basetest_test\.', '', str(e))
      self.assertRegexpMatches(error_msg, """(?m)\
{<.*RaisesOnRepr object.*>: <.*RaisesOnRepr object.*>} != \
{<.*RaisesOnRepr object.*>: <.*RaisesOnRepr object.*>}
Unexpected, but present entries:
<.*RaisesOnRepr object.*>: <.*RaisesOnRepr object.*>

Missing entries:
<.*RaisesOnRepr object.*>: <.*RaisesOnRepr object.*>
""")

    # Confirm that safe_repr, not repr, is being used.
    class RaisesOnLt(object):

      def __lt__(self):
        raise TypeError('Object is unordered.')

      def __repr__(self):
        return '<RaisesOnLt object>'

    try:
      self.assertDictEqual(
          {RaisesOnLt(): RaisesOnLt()},
          {RaisesOnLt(): RaisesOnLt()})
    except AssertionError as e:
      self.assertIn('Unexpected, but present entries:\n<RaisesOnLt', str(e))
      self.assertIn('Missing entries:\n<RaisesOnLt', str(e))

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
    self.assertContainsSubset({'a', 'b'}, actual)
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
                                     self.assertContainsSubset, {1, 2, 3},
                                     {1, 2})
    self.assertRaisesWithRegexpMatch(
        AssertionError, 'Custom message: Missing elements',
        self.assertContainsSubset, {1, 2}, {1}, 'Custom message')

  def testAssertNoCommonElements(self):
    actual = ('a', 'b', 'c')
    self.assertNoCommonElements((), actual)
    self.assertNoCommonElements(('d', 'e'), actual)
    self.assertNoCommonElements({'d', 'e'}, actual)

    self.assertRaisesWithRegexpMatch(
        AssertionError, 'Custom message: Common elements',
        self.assertNoCommonElements, {1, 2}, {1}, 'Custom message')

    with self.assertRaises(AssertionError):
      self.assertNoCommonElements(['a'], actual)

    with self.assertRaises(AssertionError):
      self.assertNoCommonElements({'a', 'b', 'c'}, actual)

    with self.assertRaises(AssertionError):
      self.assertNoCommonElements({'b', 'c'}, set(actual))

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

  def testAssertStartsWith(self):
    self.assertStartsWith('foobar', 'foo')
    self.assertStartsWith('foobar', 'foobar')
    self.assertRaises(AssertionError, self.assertStartsWith, 'foobar', 'bar')
    self.assertRaises(AssertionError, self.assertStartsWith, 'foobar', 'blah')

  def testAssertNotStartsWith(self):
    self.assertNotStartsWith('foobar', 'bar')
    self.assertNotStartsWith('foobar', 'blah')
    self.assertRaises(AssertionError, self.assertNotStartsWith, 'foobar', 'foo')
    self.assertRaises(AssertionError, self.assertNotStartsWith, 'foobar',
                      'foobar')

  def testAssertEndsWith(self):
    self.assertEndsWith('foobar', 'bar')
    self.assertEndsWith('foobar', 'foobar')
    self.assertRaises(AssertionError, self.assertEndsWith, 'foobar', 'foo')
    self.assertRaises(AssertionError, self.assertEndsWith, 'foobar', 'blah')

  def testAssertNotEndsWith(self):
    self.assertNotEndsWith('foobar', 'foo')
    self.assertNotEndsWith('foobar', 'blah')
    self.assertRaises(AssertionError, self.assertNotEndsWith, 'foobar', 'bar')
    self.assertRaises(AssertionError, self.assertNotEndsWith, 'foobar',
                      'foobar')

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
        'regexes is a string;.*',
        self.assertRegexMatch, '1.*2', '1 2')

  def testAssertRegexMatch_unicodeVsBytes(self):
    """Ensure proper utf-8 encoding or decoding happens automatically."""
    self.assertRegexMatch(u'str', [b'str'])
    self.assertRegexMatch(b'str', [u'str'])

  def testAssertRegexMatch_unicode(self):
    self.assertRegexMatch(u'foo str', [u'str'])

  def testAssertRegexMatch_bytes(self):
    self.assertRegexMatch(b'foo str', [b'str'])

  def testAssertRegexMatch_allTheSameType(self):
    self.assertRaisesWithRegexpMatch(
        AssertionError, 'regexes .* same type',
        self.assertRegexMatch, 'foo str', [b'str', u'foo'])

  def testAssertCommandFailsStderr(self):
    # TODO(user): Gross!  These should use sys.executable instead of
    # depending on /usr/bin/perl existing.
    self.assertCommandFails(
        ['/usr/bin/perl', '-e', 'die "FAIL";'],
        [r'(.|\n)*FAIL at -e line 1\.'])

  def testAssertCommandFailsWithListOfString(self):
    self.assertCommandFails(['false'], [''])

  def testAssertCommandFailsWithListOfUnicodeString(self):
    self.assertCommandFails([u'false'], [''])

  def testAssertCommandFailsWithUnicodeString(self):
    self.assertCommandFails(u'false', [u''])

  def testAssertCommandFailsWithUnicodeStringBytesRegex(self):
    self.assertCommandFails(u'false', [b''])

  def testAssertCommandSucceedsStderr(self):
    expected_re = re.compile(r'(.|\n)*FAIL at -e line 1\.', re.MULTILINE)

    self.assertRaisesWithRegexpMatch(
        AssertionError,
        expected_re,
        self.assertCommandSucceeds,
        ['/usr/bin/perl', '-e', 'die "FAIL";'])

  def testAssertCommandSucceedsWithMatchingUnicodeRegexes(self):
    self.assertCommandSucceeds(['echo', 'SUCCESS'], regexes=[u'SUCCESS'])

  def testAssertCommandSucceedsWithMatchingBytesRegexes(self):
    self.assertCommandSucceeds(['echo', 'SUCCESS'], regexes=[b'SUCCESS'])

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
    with self.assertRaisesRegexp(AssertionError, '^Exception not raised$'):
      self.assertRaisesWithPredicateMatch(Exception,
                                          lambda e: True,
                                          lambda: 1)  # don't raise

    with self.assertRaisesRegexp(AssertionError, '^Exception not raised$'):
      with self.assertRaisesWithPredicateMatch(Exception, lambda e: True):
        pass  # don't raise

  def testAssertRaisesWithPredicateMatch_raisesWrongExceptionFails(self):
    def _RaiseValueError():
      raise ValueError

    with self.assertRaises(ValueError):
      self.assertRaisesWithPredicateMatch(IOError,
                                          lambda e: True,
                                          _RaiseValueError)

    with self.assertRaises(ValueError):
      with self.assertRaisesWithPredicateMatch(IOError, lambda e: True):
        raise ValueError

  def testAssertRaisesWithPredicateMatch_predicateFails(self):
    def _RaiseValueError():
      raise ValueError
    with self.assertRaisesRegexp(AssertionError, ' does not match predicate '):
      self.assertRaisesWithPredicateMatch(ValueError,
                                          lambda e: False,
                                          _RaiseValueError)

    with self.assertRaisesRegexp(AssertionError, ' does not match predicate '):
      with self.assertRaisesWithPredicateMatch(ValueError, lambda e: False):
        raise ValueError

  def testAssertRaisesWithPredicateMatch_predicatePasses(self):
    def _RaiseValueError():
      raise ValueError

    self.assertRaisesWithPredicateMatch(ValueError,
                                        lambda e: True,
                                        _RaiseValueError)

    with self.assertRaisesWithPredicateMatch(ValueError, lambda e: True):
      raise ValueError

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
        AssertionError, '^Exception not raised',
        self.assertRaisesWithRegexpMatch, Exception, re.compile('x'),
        lambda: None)
    self.assertRaisesWithRegexpMatch(
        AssertionError, '^Exception not raised',
        self.assertRaisesWithRegexpMatch, Exception, 'x', lambda: None)
    self.assertRaisesWithRegexpMatch(
        AssertionError, '^Exception not raised',
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

  def testAssertContainsSubsequenceForNumbers(self):
    self.assertContainsSubsequence([1, 2, 3], [1])
    self.assertContainsSubsequence([1, 2, 3], [1, 2])
    self.assertContainsSubsequence([1, 2, 3], [1, 3])

    with self.assertRaises(AssertionError):
      self.assertContainsSubsequence([1, 2, 3], [4])
    with self.assertRaises(AssertionError):
      self.assertContainsSubsequence([1, 2, 3], [3, 1])

  def testAssertContainsSubsequenceForStrings(self):
    self.assertContainsSubsequence(['foo', 'bar', 'blorp'], ['foo', 'blorp'])
    with self.assertRaises(AssertionError):
      self.assertContainsSubsequence(
          ['foo', 'bar', 'blorp'], ['blorp', 'foo'])

  def testAssertContainsSubsequenceWithEmptySubsequence(self):
    self.assertContainsSubsequence([1, 2, 3], [])
    self.assertContainsSubsequence(['foo', 'bar', 'blorp'], [])
    self.assertContainsSubsequence([], [])

  def testAssertContainsSubsequenceWithEmptyContainer(self):
    with self.assertRaises(AssertionError):
      self.assertContainsSubsequence([], [1])
    with self.assertRaises(AssertionError):
      self.assertContainsSubsequence([], ['foo'])

  def testAssertTotallyOrdered(self):
    # Valid.
    self.assertTotallyOrdered()
    self.assertTotallyOrdered([1])
    self.assertTotallyOrdered([1], [2])
    self.assertTotallyOrdered([1, 1, 1])
    self.assertTotallyOrdered([(1, 1)], [(1, 2)], [(2, 1)])
    if PY_VERSION_2:
      # In Python 3 comparing different types of elements is not supported.
      self.assertTotallyOrdered([None], [1], [2])
      self.assertTotallyOrdered([1, 1, 1], ['a string'])

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

    if PY_VERSION_2:
      self.assertTotallyOrdered(
          [None],  # None should come before everything else.
          [1],     # Integers sort earlier.
          [A(1, 'a')],
          [A(2, 'b')],  # 2 is after 1.
          [A(3, 'c'), A(3, 'd')],  # The second argument is irrelevant.
          [A(4, 'z')],
          ['foo'])  # Strings sort last.
    else:
      # Python 3 does not define ordering across different types.
      self.assertTotallyOrdered(
          [A(1, 'a')],
          [A(2, 'b')],  # 2 is after 1.
          [A(3, 'c'), A(3, 'd')],  # The second argument is irrelevant.
          [A(4, 'z')])

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

  def testAssertUrlEqualSame(self):
    self.assertUrlEqual('http://a', 'http://a')
    self.assertUrlEqual('http://a/path/test', 'http://a/path/test')
    self.assertUrlEqual('#fragment', '#fragment')
    self.assertUrlEqual('http://a/?q=1', 'http://a/?q=1')
    self.assertUrlEqual('http://a/?q=1&v=5', 'http://a/?v=5&q=1')
    self.assertUrlEqual('/logs?v=1&a=2&t=labels&f=path%3A%22foo%22',
                        '/logs?a=2&f=path%3A%22foo%22&v=1&t=labels')
    self.assertUrlEqual('http://a/path;p1', 'http://a/path;p1')
    self.assertUrlEqual('http://a/path;p2;p3;p1', 'http://a/path;p1;p2;p3')
    self.assertUrlEqual('sip:alice@atlanta.com;maddr=239.255.255.1;ttl=15',
                        'sip:alice@atlanta.com;ttl=15;maddr=239.255.255.1')
    self.assertUrlEqual('http://nyan/cat?p=1&b=', 'http://nyan/cat?b=&p=1')

  def testAssertUrlEqualDifferent(self):
    self.assertRaises(AssertionError, self.assertUrlEqual,
                      'http://a', 'http://b')
    self.assertRaises(AssertionError, self.assertUrlEqual,
                      'http://a/x', 'http://a:8080/x')
    self.assertRaises(AssertionError, self.assertUrlEqual,
                      'http://a/x', 'http://a/y')
    self.assertRaises(AssertionError, self.assertUrlEqual,
                      'http://a/?q=2', 'http://a/?q=1')
    self.assertRaises(AssertionError, self.assertUrlEqual,
                      'http://a/?q=1&v=5', 'http://a/?v=2&q=1')
    self.assertRaises(AssertionError, self.assertUrlEqual,
                      'http://a', 'sip://b')
    self.assertRaises(AssertionError, self.assertUrlEqual,
                      'http://a#g', 'sip://a#f')
    self.assertRaises(AssertionError, self.assertUrlEqual,
                      'http://a/path;p1;p3;p1', 'http://a/path;p1;p2;p3')
    self.assertRaises(AssertionError, self.assertUrlEqual,
                      'http://nyan/cat?p=1&b=', 'http://nyan/cat?p=1')

  def testSameStructure_same(self):
    self.assertSameStructure(0, 0)
    self.assertSameStructure(1, 1)
    self.assertSameStructure('', '')
    self.assertSameStructure('hello', 'hello', msg='This Should not fail')
    self.assertSameStructure(set(), set())
    self.assertSameStructure(set([1, 2]), set([1, 2]))
    self.assertSameStructure([], [])
    self.assertSameStructure(['a'], ['a'])
    self.assertSameStructure({}, {})
    self.assertSameStructure({'one': 1}, {'one': 1})
    # int and long should always be treated as the same type.
    self.assertSameStructure({3L: 3}, {3: 3L})

  def testSameStructure_different(self):
    # Different type
    self.assertRaisesWithRegexpMatch(
        AssertionError,
        r"a is a <(type|class) 'int'> but b is a <(type|class) 'str'>",
        self.assertSameStructure, 0, 'hello')
    self.assertRaisesWithRegexpMatch(
        AssertionError,
        r"a is a <(type|class) 'int'> but b is a <(type|class) 'list'>",
        self.assertSameStructure, 0, [])
    self.assertRaisesWithRegexpMatch(
        AssertionError,
        r"a is a <(type|class) 'int'> but b is a <(type|class) 'float'>",
        self.assertSameStructure, 2, 2.0)

    # Different scalar values
    self.assertRaisesWithLiteralMatch(
        AssertionError, 'a is 0 but b is 1',
        self.assertSameStructure, 0, 1)
    self.assertRaisesWithLiteralMatch(
        AssertionError, "a is 'hello' but b is 'goodbye': This was expected",
        self.assertSameStructure, 'hello', 'goodbye', msg='This was expected')

    # Different sets are treated without structure
    self.assertRaisesWithRegexpMatch(
        AssertionError, r'AA is (set\(\[1\]\)|\{1\}) but BB is set\((\[\])?\)',
        self.assertSameStructure, set([1]), set(), aname='AA', bname='BB')

    # Different lists
    self.assertRaisesWithLiteralMatch(
        AssertionError, 'a has [2] but b does not',
        self.assertSameStructure, ['x', 'y', 'z'], ['x', 'y'])
    self.assertRaisesWithLiteralMatch(
        AssertionError, 'a lacks [2] but b has it',
        self.assertSameStructure, ['x', 'y'], ['x', 'y', 'z'])
    self.assertRaisesWithLiteralMatch(
        AssertionError, "a[2] is 'z' but b[2] is 'Z'",
        self.assertSameStructure, ['x', 'y', 'z'], ['x', 'y', 'Z'])

    # Different dicts
    self.assertRaisesWithLiteralMatch(
        AssertionError, "a has ['two'] but b does not",
        self.assertSameStructure, {'one': 1, 'two': 2}, {'one': 1})
    self.assertRaisesWithLiteralMatch(
        AssertionError, "a lacks ['two'] but b has it",
        self.assertSameStructure, {'one': 1}, {'one': 1, 'two': 2})
    self.assertRaisesWithLiteralMatch(
        AssertionError, "a['two'] is 2 but b['two'] is 3",
        self.assertSameStructure, {'one': 1, 'two': 2}, {'one': 1, 'two': 3})

    # Deep key generation
    self.assertRaisesWithLiteralMatch(
        AssertionError,
        "a[0][0]['x']['y']['z'][0] is 1 but b[0][0]['x']['y']['z'][0] is 2",
        self.assertSameStructure,
        [[{'x': {'y': {'z': [1]}}}]], [[{'x': {'y': {'z': [2]}}}]])

    # Multiple problems
    self.assertRaisesWithLiteralMatch(
        AssertionError,
        'a[0] is 1 but b[0] is 3; a[1] is 2 but b[1] is 4',
        self.assertSameStructure, [1, 2], [3, 4])
    self.assertRaisesWithRegexpMatch(
        AssertionError,
        re.compile(r"^a\[0] is 'a' but b\[0] is 'A'; .*"
                   r"a\[18] is 's' but b\[18] is 'S'; \.\.\.$"),
        self.assertSameStructure,
        list(string.ascii_lowercase), list(string.ascii_uppercase))

  def testAssertJsonEqualSame(self):
    self.assertJsonEqual('{"success": true}', '{"success": true}')
    self.assertJsonEqual('{"success": true}', '{"success":true}')
    self.assertJsonEqual('true', 'true')
    self.assertJsonEqual('null', 'null')
    self.assertJsonEqual('false', 'false')
    self.assertJsonEqual('34', '34')
    self.assertJsonEqual('[1, 2, 3]', '[1,2,3]', msg='please PASS')
    self.assertJsonEqual('{"sequence": [1, 2, 3], "float": 23.42}',
                         '{"float": 23.42, "sequence": [1,2,3]}')
    self.assertJsonEqual('{"nest": {"spam": "eggs"}, "float": 23.42}',
                         '{"float": 23.42, "nest": {"spam":"eggs"}}')

  def testAssertJsonEqualDifferent(self):
    with self.assertRaises(AssertionError):
      self.assertJsonEqual('{"success": true}', '{"success": false}')
    with self.assertRaises(AssertionError):
      self.assertJsonEqual('{"success": false}', '{"Success": false}')
    with self.assertRaises(AssertionError):
      self.assertJsonEqual('false', 'true')
    with self.assertRaises(AssertionError) as error_context:
      self.assertJsonEqual('null', '0', msg='I demand FAILURE')
    self.assertIn('I demand FAILURE', error_context.exception.args[0])
    self.assertIn('None', error_context.exception.args[0])
    with self.assertRaises(AssertionError):
      self.assertJsonEqual('[1, 0, 3]', '[1,2,3]')
    with self.assertRaises(AssertionError):
      self.assertJsonEqual('{"sequence": [1, 2, 3], "float": 23.42}',
                           '{"float": 23.42, "sequence": [1,0,3]}')
    with self.assertRaises(AssertionError):
      self.assertJsonEqual('{"nest": {"spam": "eggs"}, "float": 23.42}',
                           '{"float": 23.42, "nest": {"Spam":"beans"}}')

  def testAssertJsonEqualBadJson(self):
    with self.assertRaises(ValueError) as error_context:
      self.assertJsonEqual("alhg'2;#", '{"a": true}')
    self.assertIn('first', error_context.exception.args[0])
    self.assertIn('alhg', error_context.exception.args[0])

    with self.assertRaises(ValueError) as error_context:
      self.assertJsonEqual('{"a": true}', "alhg'2;#")
    self.assertIn('second', error_context.exception.args[0])
    self.assertIn('alhg', error_context.exception.args[0])

    with self.assertRaises(ValueError) as error_context:
      self.assertJsonEqual('', '')


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

  class EqualityTestsWithLtEq(object):

    def __init__(self, value):
      self._value = value

    def __eq__(self, other):
      return self._value == other._value

    def __lt__(self, other):
      return self._value < other._value

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
    if PY_VERSION_2:
      # Python 3 removes the global cmp function
      self.assertEqual(0, cmp(same_a, same_b))

    self.assertFalse(same_a == different)
    self.assertTrue(same_a != different)
    self.assertNotEqual(same_a, different)
    self.assertNotEquals(same_a, different)
    self.failIfEqual(same_a, different)
    if PY_VERSION_2:
      self.assertNotEqual(0, cmp(same_a, different))

    self.assertFalse(same_b == different)
    self.assertTrue(same_b != different)
    self.assertNotEqual(same_b, different)
    self.assertNotEquals(same_b, different)
    self.failIfEqual(same_b, different)
    if PY_VERSION_2:
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

  def testComparisonWithCmpOrLtEq(self):
    if PY_VERSION_2:
      # In Python 3; the __cmp__ method is no longer special.
      cmp_or_lteq_class = self.EqualityTestsWithCmp
    else:
      cmp_or_lteq_class = self.EqualityTestsWithLtEq

    same_a = cmp_or_lteq_class(42)
    same_b = cmp_or_lteq_class(42)
    different = cmp_or_lteq_class(1769)
    self._PerformAppleAppleOrangeChecks(same_a, same_b, different)


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
           '<(type|class) \'int\'>')
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
  """TestCase assertions should work even if __init__ wasn't correctly called.

  This is a hack, see comment in
  basetest.TestCase._getAssertEqualityFunc. We know that not calling
  __init__ of a superclass is a bad thing, but people keep doing them,
  and this (even if a little bit dirty) saves them from shooting
  themselves in the foot.
  """

  def testSubclass(self):

    class Subclass(basetest.TestCase):

      def __init__(self):  # pylint: disable=super-init-not-called
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
