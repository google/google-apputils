#!/usr/bin/env python
# Copyright 2002 Google Inc. All Rights Reserved.
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

"""Unittest for datelib.py module."""



import random
import time

import pytz

from google.apputils import basetest
from google.apputils import datelib


class TimestampUnitTest(basetest.TestCase):
  seed = 1979

  def testTzAwareSuccession(self):
    a = datelib.Timestamp.now()
    b = datelib.Timestamp.utcnow()

    self.assertLessEqual(a, b)

  def testTzRandomConversion(self):
    random.seed(self.seed)
    for unused_i in xrange(100):
      stz = pytz.timezone(random.choice(pytz.all_timezones))
      a = datelib.Timestamp.FromString('2008-04-12T10:00:00', stz)

      b = a
      for unused_j in xrange(100):
        b = b.astimezone(pytz.timezone(random.choice(pytz.all_timezones)))
        self.assertEqual(a, b)
    random.seed()

  def testMicroTimestampConversion(self):
    """Test that f1(f2(a)) == a."""

    def IsEq(x):
      self.assertEqual(
          x, datelib.Timestamp.FromMicroTimestamp(x).AsMicroTimestamp())

    IsEq(0)
    IsEq(datelib.MAXIMUM_MICROSECOND_TIMESTAMP)

    random.seed(self.seed)
    for _ in xrange(100):
      IsEq(random.randint(0, datelib.MAXIMUM_MICROSECOND_TIMESTAMP))

  def testMicroTimestampKnown(self):
    self.assertEqual(0, datelib.Timestamp.FromString(
        '1970-01-01T00:00:00', pytz.UTC).AsMicroTimestamp())

    self.assertEqual(
        datelib.MAXIMUM_MICROSECOND_TIMESTAMP,
        datelib.MAXIMUM_MICROSECOND_TIMESTAMP_AS_TS.AsMicroTimestamp())

  def testMicroTimestampOrdering(self):
    """Test that cmp(a, b) == cmp(f1(a), f1(b))."""

    def IsEq(a, b):
      self.assertEqual(
          cmp(a, b),
          cmp(datelib.Timestamp.FromMicroTimestamp(a),
              datelib.Timestamp.FromMicroTimestamp(b)))

    random.seed(self.seed)
    for unused_i in xrange(100):
      IsEq(
          random.randint(0, datelib.MAXIMUM_MICROSECOND_TIMESTAMP),
          random.randint(0, datelib.MAXIMUM_MICROSECOND_TIMESTAMP))

  def testCombine(self):
    for tz in (datelib.UTC, datelib.US_PACIFIC):
      self.assertEqual(
          datelib.Timestamp(1970, 1, 1, 0, 0, 0, 0, tz),
          datelib.Timestamp.combine(
              datelib.datetime.date(1970, 1, 1),
              datelib.datetime.time(0, 0, 0),
              tz))

      self.assertEqual(
          datelib.Timestamp(9998, 12, 31, 23, 59, 59, 999999, tz),
          datelib.Timestamp.combine(
              datelib.datetime.date(9998, 12, 31),
              datelib.datetime.time(23, 59, 59, 999999),
              tz))

  def testFromString1(self):
    for string_zero in (
        '1970-01-01 00:00:00',
        '19700101T000000',
        '1970-01-01T00:00:00'
        ):
      for testtz in (datelib.UTC, datelib.US_PACIFIC):
        self.assertEqual(
            datelib.Timestamp.FromString(string_zero, testtz),
            datelib.Timestamp(1970, 1, 1, 0, 0, 0, 0, testtz))

    self.assertEqual(
        datelib.Timestamp.FromString(
            '1970-01-01T00:00:00+0000', datelib.US_PACIFIC),
        datelib.Timestamp(1970, 1, 1, 0, 0, 0, 0, datelib.UTC))

    startdate = datelib.Timestamp(2009, 1, 1, 3, 0, 0, 0, datelib.US_PACIFIC)
    for day in xrange(1, 366):
      self.assertEqual(
          datelib.Timestamp.FromString(startdate.isoformat()),
          startdate,
          'FromString works for day %d since 2009-01-01' % day)
      startdate += datelib.datetime.timedelta(days=1)

  def testFromString2(self):
    """Test correctness of parsing the local time in a given timezone.

    The result shall always be the same as tz.localize(naive_time).
    """
    baseday = datelib.datetime.date(2009, 1, 1).toordinal()
    for day_offset in xrange(0, 365):
      day = datelib.datetime.date.fromordinal(baseday + day_offset)
      naive_day = datelib.datetime.datetime.combine(
          day, datelib.datetime.time(0, 45, 9))

      naive_day_str = naive_day.strftime('%Y-%m-%dT%H:%M:%S')

      self.assertEqual(
          datelib.US_PACIFIC.localize(naive_day),
          datelib.Timestamp.FromString(naive_day_str, tz=datelib.US_PACIFIC),
          'FromString localizes time incorrectly')


if __name__ == '__main__':
  basetest.main()
