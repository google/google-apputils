#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test for google.apputils.humanize."""



import datetime
from google.apputils import basetest
from google.apputils import datelib
from google.apputils import humanize


class HumanizeTest(basetest.TestCase):

  def testCommas(self):
    self.assertEqual('0', humanize.Commas(0))
    self.assertEqual('100', humanize.Commas(100))
    self.assertEqual('1,000', humanize.Commas(1000))
    self.assertEqual('10,000', humanize.Commas(10000))
    self.assertEqual('1,000,000', humanize.Commas(1e6))
    self.assertEqual('-1,000,000', humanize.Commas(-1e6))

  def testPlural(self):
    self.assertEqual('0 objects', humanize.Plural(0, 'object'))
    self.assertEqual('1 object', humanize.Plural(1, 'object'))
    self.assertEqual('-1 objects', humanize.Plural(-1, 'object'))
    self.assertEqual('42 objects', humanize.Plural(42, 'object'))
    self.assertEqual('42 cats', humanize.Plural(42, 'cat'))
    self.assertEqual('42 glasses', humanize.Plural(42, 'glass'))
    self.assertEqual('42 potatoes', humanize.Plural(42, 'potato'))
    self.assertEqual('42 cherries', humanize.Plural(42, 'cherry'))
    self.assertEqual('42 monkeys', humanize.Plural(42, 'monkey'))
    self.assertEqual('42 oxen', humanize.Plural(42, 'ox', 'oxen'))
    self.assertEqual('42 indices', humanize.Plural(42, 'index'))
    self.assertEqual(
        '42 attorneys general',
        humanize.Plural(42, 'attorney general', 'attorneys general'))

  def testPluralWord(self):
    self.assertEqual('vaxen', humanize.PluralWord(2, 'vax', plural='vaxen'))
    self.assertEqual('cores', humanize.PluralWord(2, 'core'))
    self.assertEqual('group', humanize.PluralWord(1, 'group'))
    self.assertEqual('cells', humanize.PluralWord(0, 'cell'))
    self.assertEqual('degree', humanize.PluralWord(1.0, 'degree'))
    self.assertEqual('helloes', humanize.PluralWord(3.14, 'hello'))

  def testWordSeries(self):
    self.assertEqual('', humanize.WordSeries([]))
    self.assertEqual('foo', humanize.WordSeries(['foo']))
    self.assertEqual('foo and bar', humanize.WordSeries(['foo', 'bar']))
    self.assertEqual(
        'foo, bar, and baz', humanize.WordSeries(['foo', 'bar', 'baz']))
    self.assertEqual(
        'foo, bar, or baz', humanize.WordSeries(['foo', 'bar', 'baz'],
                                                conjunction='or'))

  def testAddIndefiniteArticle(self):
    self.assertEqual('a thing', humanize.AddIndefiniteArticle('thing'))
    self.assertEqual('an object', humanize.AddIndefiniteArticle('object'))
    self.assertEqual('a Porsche', humanize.AddIndefiniteArticle('Porsche'))
    self.assertEqual('an Audi', humanize.AddIndefiniteArticle('Audi'))

  def testDecimalPrefix(self):
    self.assertEqual('0 m', humanize.DecimalPrefix(0, 'm'))
    self.assertEqual('1 km', humanize.DecimalPrefix(1000, 'm'))
    self.assertEqual('-1 km', humanize.DecimalPrefix(-1000, 'm'))
    self.assertEqual('10 Gbps', humanize.DecimalPrefix(10e9, 'bps'))
    self.assertEqual('6000 Yg', humanize.DecimalPrefix(6e27, 'g'))
    self.assertEqual('12.1 km', humanize.DecimalPrefix(12100, 'm', precision=3))
    self.assertEqual('12 km', humanize.DecimalPrefix(12100, 'm', precision=2))
    self.assertEqual('1.15 km', humanize.DecimalPrefix(1150, 'm', precision=3))
    self.assertEqual('-1.15 km', humanize.DecimalPrefix(-1150, 'm',
                                                        precision=3))
    self.assertEqual('1 k', humanize.DecimalPrefix(1000, ''))
    self.assertEqual('-10 G', humanize.DecimalPrefix(-10e9, ''))
    self.assertEqual('12', humanize.DecimalPrefix(12, ''))
    self.assertEqual('-115', humanize.DecimalPrefix(-115, ''))
    self.assertEqual('0', humanize.DecimalPrefix(0, ''))

    self.assertEqual('1.1 s', humanize.DecimalPrefix(1.12, 's', precision=2))
    self.assertEqual('-1.1 s', humanize.DecimalPrefix(-1.12, 's', precision=2))
    self.assertEqual('nan bps', humanize.DecimalPrefix(float('nan'), 'bps'))
    self.assertEqual('nan', humanize.DecimalPrefix(float('nan'), ''))
    self.assertEqual('inf bps', humanize.DecimalPrefix(float('inf'), 'bps'))
    self.assertEqual('-inf bps', humanize.DecimalPrefix(float('-inf'), 'bps'))
    self.assertEqual('-inf', humanize.DecimalPrefix(float('-inf'), ''))

    self.assertEqual('-4 mm',
                     humanize.DecimalPrefix(-0.004, 'm', min_scale=None))
    self.assertEqual('0 m', humanize.DecimalPrefix(0, 'm', min_scale=None))
    self.assertEqual(
        u'1 µs',
        humanize.DecimalPrefix(0.0000013, 's', min_scale=None))
    self.assertEqual('3 km', humanize.DecimalPrefix(3000, 'm', min_scale=None))
    self.assertEqual(
        '5000 TB',
        humanize.DecimalPrefix(5e15, 'B', max_scale=4))
    self.assertEqual(
        '5 mSWE',
        humanize.DecimalPrefix(0.005, 'SWE', min_scale=None))
    self.assertEqual(
        '0.0005 ms',
        humanize.DecimalPrefix(5e-7, 's', min_scale=-1, precision=2))

  def testBinaryPrefix(self):
    self.assertEqual('0 B', humanize.BinaryPrefix(0, 'B'))
    self.assertEqual('1000 B', humanize.BinaryPrefix(1000, 'B'))
    self.assertEqual('1 KiB', humanize.BinaryPrefix(1024, 'B'))
    self.assertEqual('64 GiB', humanize.BinaryPrefix(2**36, 'B'))
    self.assertEqual('65536 Yibit', humanize.BinaryPrefix(2**96, 'bit'))
    self.assertEqual('1.25 KiB', humanize.BinaryPrefix(1280, 'B', precision=3))
    self.assertEqual('1.2 KiB', humanize.BinaryPrefix(1280, 'B', precision=2))
    self.assertEqual('1.2 Ki', humanize.BinaryPrefix(1280, '', precision=2))
    self.assertEqual('12', humanize.BinaryPrefix(12, '', precision=2))

    # Test both int and long versions of the same quantity to make sure they are
    # printed in the same way.
    self.assertEqual('10.0 QPS', humanize.BinaryPrefix(10, 'QPS', precision=3))
    self.assertEqual('10.0 QPS', humanize.BinaryPrefix(10L, 'QPS', precision=3))

  def testDecimalScale(self):
    self.assertIsInstance(humanize.DecimalScale(0, '')[0], float)
    self.assertIsInstance(humanize.DecimalScale(1, '')[0], float)
    self.assertEqual((12.1, 'km'), humanize.DecimalScale(12100, 'm'))
    self.assertEqual((12.1, 'k'), humanize.DecimalScale(12100, ''))
    self.assertEqual((0, ''), humanize.DecimalScale(0, ''))
    self.assertEqual(
        (12.1, 'km'),
        humanize.DecimalScale(12100, 'm', min_scale=0, max_scale=None))
    self.assertEqual(
        (12100, 'm'),
        humanize.DecimalScale(12100, 'm', min_scale=0, max_scale=0))
    self.assertEqual((1.15, 'Mm'), humanize.DecimalScale(1150000, 'm'))
    self.assertEqual((1, 'm'),
                     humanize.DecimalScale(1, 'm', min_scale=None))
    self.assertEqual((450, 'mSWE'),
                     humanize.DecimalScale(0.45, 'SWE', min_scale=None))
    self.assertEqual(
        (250, u'µm'),
        humanize.DecimalScale(1.0 / (4 * 1000), 'm', min_scale=None))
    self.assertEqual(
        (0.250, 'km'),
        humanize.DecimalScale(250, 'm', min_scale=1))
    self.assertEqual(
        (12000, 'mm'),
        humanize.DecimalScale(12, 'm', min_scale=None, max_scale=-1))

  def testBinaryScale(self):
    self.assertIsInstance(humanize.BinaryScale(0, '')[0], float)
    self.assertIsInstance(humanize.BinaryScale(1, '')[0], float)
    value, unit = humanize.BinaryScale(200000000000, 'B')
    self.assertAlmostEqual(value, 186.26, 2)
    self.assertEqual(unit, 'GiB')

    value, unit = humanize.BinaryScale(3000000000000, 'B')
    self.assertAlmostEqual(value, 2.728, 3)
    self.assertEqual(unit, 'TiB')

  def testPrettyFraction(self):
    # No rounded integer part
    self.assertEqual(u'½', humanize.PrettyFraction(0.5))
    # Roundeded integer + fraction
    self.assertEqual(u'6⅔', humanize.PrettyFraction(20.0 / 3.0))
    # Rounded integer, no fraction
    self.assertEqual(u'2', humanize.PrettyFraction(2.00001))
    # No rounded integer, no fraction
    self.assertEqual(u'0', humanize.PrettyFraction(0.001))
    # Round up
    self.assertEqual(u'1', humanize.PrettyFraction(0.99))
    # No round up, edge case
    self.assertEqual(u'⅞', humanize.PrettyFraction(0.9))
    # Negative fraction
    self.assertEqual(u'-⅕', humanize.PrettyFraction(-0.2))
    # Negative close to zero (should not be -0)
    self.assertEqual(u'0', humanize.PrettyFraction(-0.001))
    # Smallest fraction that should round down.
    self.assertEqual(u'0', humanize.PrettyFraction(1.0 / 16.0))
    # Largest fraction should round up.
    self.assertEqual(u'1', humanize.PrettyFraction(15.0 / 16.0))
    # Integer zero.
    self.assertEqual(u'0', humanize.PrettyFraction(0))
    # Check that division yields fraction
    self.assertEqual(u'⅘', humanize.PrettyFraction(4.0 / 5.0))
    # Custom spacer.
    self.assertEqual(u'2 ½', humanize.PrettyFraction(2.5, spacer=' '))

  def testDuration(self):
    self.assertEqual('2h', humanize.Duration(7200))
    self.assertEqual('5d 13h 47m 12s', humanize.Duration(481632))
    self.assertEqual('0s', humanize.Duration(0))
    self.assertEqual('59s', humanize.Duration(59))
    self.assertEqual('1m', humanize.Duration(60))
    self.assertEqual('1m 1s', humanize.Duration(61))
    self.assertEqual('1h 1s', humanize.Duration(3601))
    self.assertEqual('2h-2s', humanize.Duration(7202, separator='-'))

  def testLargeDuration(self):
    # The maximum seconds and days that can be stored in a datetime.timedelta
    # object, as seconds.  max_days is equal to MAX_DELTA_DAYS in Python's
    # Modules/datetimemodule.c, converted to seconds.
    max_seconds = 3600 * 24 - 1
    max_days = 999999999 * 24 * 60 * 60

    self.assertEqual('999999999d', humanize.Duration(max_days))
    self.assertEqual('999999999d 23h 59m 59s',
                     humanize.Duration(max_days + max_seconds))
    self.assertEqual('>=999999999d 23h 59m 60s',
                     humanize.Duration(max_days + max_seconds + 1))

  def testTimeDelta(self):
    self.assertEqual('0s', humanize.TimeDelta(datetime.timedelta()))
    self.assertEqual('2h', humanize.TimeDelta(datetime.timedelta(hours=2)))
    self.assertEqual('1m', humanize.TimeDelta(datetime.timedelta(minutes=1)))
    self.assertEqual('5d', humanize.TimeDelta(datetime.timedelta(days=5)))
    self.assertEqual('1.25s', humanize.TimeDelta(
        datetime.timedelta(seconds=1, microseconds=250000)))
    self.assertEqual('1.5s',
                     humanize.TimeDelta(datetime.timedelta(seconds=1.5)))
    self.assertEqual('4d 10h 5m 12.25s', humanize.TimeDelta(
        datetime.timedelta(days=4, hours=10, minutes=5, seconds=12,
                           microseconds=250000)))

  def testUnixTimestamp(self):
    self.assertEqual('2013-11-17 11:08:27.723524 PST',
                     humanize.UnixTimestamp(1384715307.723524,
                                            datelib.US_PACIFIC))
    self.assertEqual('2013-11-17 19:08:27.723524 UTC',
                     humanize.UnixTimestamp(1384715307.723524,
                                            datelib.UTC))

    # DST part of the timezone should not depend on the current local time,
    # so this should be in PDT (and different from the PST in the first test).
    self.assertEqual('2013-05-17 15:47:21.723524 PDT',
                     humanize.UnixTimestamp(1368830841.723524,
                                            datelib.US_PACIFIC))

    self.assertEqual('1970-01-01 00:00:00.000000 UTC',
                     humanize.UnixTimestamp(0, datelib.UTC))

  def testAddOrdinalSuffix(self):
    self.assertEqual('0th', humanize.AddOrdinalSuffix(0))
    self.assertEqual('1st', humanize.AddOrdinalSuffix(1))
    self.assertEqual('2nd', humanize.AddOrdinalSuffix(2))
    self.assertEqual('3rd', humanize.AddOrdinalSuffix(3))
    self.assertEqual('4th', humanize.AddOrdinalSuffix(4))
    self.assertEqual('5th', humanize.AddOrdinalSuffix(5))
    self.assertEqual('10th', humanize.AddOrdinalSuffix(10))
    self.assertEqual('11th', humanize.AddOrdinalSuffix(11))
    self.assertEqual('12th', humanize.AddOrdinalSuffix(12))
    self.assertEqual('13th', humanize.AddOrdinalSuffix(13))
    self.assertEqual('14th', humanize.AddOrdinalSuffix(14))
    self.assertEqual('20th', humanize.AddOrdinalSuffix(20))
    self.assertEqual('21st', humanize.AddOrdinalSuffix(21))
    self.assertEqual('22nd', humanize.AddOrdinalSuffix(22))
    self.assertEqual('23rd', humanize.AddOrdinalSuffix(23))
    self.assertEqual('24th', humanize.AddOrdinalSuffix(24))
    self.assertEqual('63rd', humanize.AddOrdinalSuffix(63))
    self.assertEqual('100000th', humanize.AddOrdinalSuffix(100000))
    self.assertEqual('100001st', humanize.AddOrdinalSuffix(100001))
    self.assertEqual('100011th', humanize.AddOrdinalSuffix(100011))
    self.assertRaises(ValueError, humanize.AddOrdinalSuffix, -1)
    self.assertRaises(ValueError, humanize.AddOrdinalSuffix, 0.5)
    self.assertRaises(ValueError, humanize.AddOrdinalSuffix, 123.001)


class NaturalSortKeyChunkingTest(basetest.TestCase):

  def testChunkifySingleChars(self):
    self.assertListEqual(
        humanize.NaturalSortKey('a1b2c3'),
        ['a', 1, 'b', 2, 'c', 3])

  def testChunkifyMultiChars(self):
    self.assertListEqual(
        humanize.NaturalSortKey('aa11bb22cc33'),
        ['aa', 11, 'bb', 22, 'cc', 33])

  def testChunkifyComplex(self):
    self.assertListEqual(
        humanize.NaturalSortKey('one 11 -- two 44'),
        ['one ', 11, ' -- two ', 44])


class NaturalSortKeysortTest(basetest.TestCase):

  def testNaturalSortKeySimpleWords(self):
    self.test = ['pair', 'banana', 'apple']
    self.good = ['apple', 'banana', 'pair']
    self.test.sort(key=humanize.NaturalSortKey)
    self.assertListEqual(self.test, self.good)

  def testNaturalSortKeySimpleNums(self):
    self.test = ['3333', '2222', '9999', '0000']
    self.good = ['0000', '2222', '3333', '9999']
    self.test.sort(key=humanize.NaturalSortKey)
    self.assertListEqual(self.test, self.good)

  def testNaturalSortKeySimpleDigits(self):
    self.test = ['8', '3', '2']
    self.good = ['2', '3', '8']
    self.test.sort(key=humanize.NaturalSortKey)
    self.assertListEqual(self.test, self.good)

  def testVersionStrings(self):
    self.test = ['1.2', '0.9', '1.1a2', '1.1a', '1', '1.2.1', '0.9.1']
    self.good = ['0.9', '0.9.1', '1', '1.1a', '1.1a2', '1.2', '1.2.1']
    self.test.sort(key=humanize.NaturalSortKey)
    self.assertListEqual(self.test, self.good)

  def testNaturalSortKeySimpleNumLong(self):
    self.test = ['11', '9', '1', '200', '19', '20', '900']
    self.good = ['1', '9', '11', '19', '20', '200', '900']
    self.test.sort(key=humanize.NaturalSortKey)
    self.assertListEqual(self.test, self.good)

  def testNaturalSortKeyAlNum(self):
    self.test = ['x10', 'x9', 'x1', 'x11']
    self.good = ['x1', 'x9', 'x10', 'x11']
    self.test.sort(key=humanize.NaturalSortKey)
    self.assertListEqual(self.test, self.good)

  def testNaturalSortKeyNumAlNum(self):
    self.test = ['4x10', '4x9', '4x11', '5yy4', '3x1', '2x11']
    self.good = ['2x11', '3x1', '4x9', '4x10', '4x11', '5yy4']
    self.test.sort(key=humanize.NaturalSortKey)
    self.assertListEqual(self.test, self.good)

  def testNaturalSortKeyAlNumAl(self):
    self.test = ['a9c', 'a4b', 'a10c', 'a1c', 'c10c', 'c10a', 'c9a']
    self.good = ['a1c', 'a4b', 'a9c', 'a10c', 'c9a', 'c10a', 'c10c']
    self.test.sort(key=humanize.NaturalSortKey)
    self.assertListEqual(self.test, self.good)


class NaturalSortKeyBigTest(basetest.TestCase):

  def testBig(self):
    self.test = [
        '1000X Radonius Maximus', '10X Radonius', '200X Radonius',
        '20X Radonius', '20X Radonius Prime', '30X Radonius',
        '40X Radonius', 'Allegia 50 Clasteron', 'Allegia 500 Clasteron',
        'Allegia 51 Clasteron', 'Allegia 51B Clasteron',
        'Allegia 52 Clasteron', 'Allegia 60 Clasteron', 'Alpha 100',
        'Alpha 2', 'Alpha 200', 'Alpha 2A', 'Alpha 2A-8000', 'Alpha 2A-900',
        'Callisto Morphamax', 'Callisto Morphamax 500',
        'Callisto Morphamax 5000', 'Callisto Morphamax 600',
        'Callisto Morphamax 700', 'Callisto Morphamax 7000',
        'Callisto Morphamax 7000 SE', 'Callisto Morphamax 7000 SE2',
        'QRS-60 Intrinsia Machine', 'QRS-60F Intrinsia Machine',
        'QRS-62 Intrinsia Machine', 'QRS-62F Intrinsia Machine',
        'Xiph Xlater 10000', 'Xiph Xlater 2000', 'Xiph Xlater 300',
        'Xiph Xlater 40', 'Xiph Xlater 5', 'Xiph Xlater 50',
        'Xiph Xlater 500', 'Xiph Xlater 5000', 'Xiph Xlater 58']
    self.good = [
        '10X Radonius',
        '20X Radonius',
        '20X Radonius Prime',
        '30X Radonius',
        '40X Radonius',
        '200X Radonius',
        '1000X Radonius Maximus',
        'Allegia 50 Clasteron',
        'Allegia 51 Clasteron',
        'Allegia 51B Clasteron',
        'Allegia 52 Clasteron',
        'Allegia 60 Clasteron',
        'Allegia 500 Clasteron',
        'Alpha 2',
        'Alpha 2A',
        'Alpha 2A-900',
        'Alpha 2A-8000',
        'Alpha 100',
        'Alpha 200',
        'Callisto Morphamax',
        'Callisto Morphamax 500',
        'Callisto Morphamax 600',
        'Callisto Morphamax 700',
        'Callisto Morphamax 5000',
        'Callisto Morphamax 7000',
        'Callisto Morphamax 7000 SE',
        'Callisto Morphamax 7000 SE2',
        'QRS-60 Intrinsia Machine',
        'QRS-60F Intrinsia Machine',
        'QRS-62 Intrinsia Machine',
        'QRS-62F Intrinsia Machine',
        'Xiph Xlater 5',
        'Xiph Xlater 40',
        'Xiph Xlater 50',
        'Xiph Xlater 58',
        'Xiph Xlater 300',
        'Xiph Xlater 500',
        'Xiph Xlater 2000',
        'Xiph Xlater 5000',
        'Xiph Xlater 10000',
        ]
    self.test.sort(key=humanize.NaturalSortKey)
    self.assertListEqual(self.test, self.good)


if __name__ == '__main__':
  basetest.main()
