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

"""Set of classes and functions for dealing with dates and timestamps.

The BaseTimestamp and Timestamp are timezone-aware wrappers around Python
datetime.datetime class.
"""



import calendar
import copy
import datetime
import re
import sys
import time
import types

from dateutil import parser
import pytz


_MICROSECONDS_PER_SECOND = 1000000
_MICROSECONDS_PER_SECOND_F = float(_MICROSECONDS_PER_SECOND)


def SecondsToMicroseconds(seconds):
  """Convert seconds to microseconds.

  Args:
    seconds: number
  Returns:
    microseconds
  """
  return seconds * _MICROSECONDS_PER_SECOND


def _GetCurrentTimeMicros():
  """Get the current time in microseconds, in UTC.

  Returns:
    The number of microseconds since the epoch.
  """
  return int(SecondsToMicroseconds(time.time()))


def GetSecondsSinceEpoch(time_tuple):
  """Convert time_tuple (in UTC) to seconds (also in UTC).

  Args:
    time_tuple: tuple with at least 6 items.
  Returns:
    seconds.
  """
  return calendar.timegm(time_tuple[:6] + (0, 0, 0))


def GetTimeMicros(time_tuple):
  """Get a time in microseconds.

  Arguments:
    time_tuple: A (year, month, day, hour, minute, second) tuple (the python
      time tuple format) in the UTC time zone.

  Returns:
    The number of microseconds since the epoch represented by the input tuple.
  """
  return int(SecondsToMicroseconds(GetSecondsSinceEpoch(time_tuple)))


UTC = pytz.UTC
US_PACIFIC = pytz.timezone('US/Pacific')


class TimestampError(ValueError):
  """Generic timestamp-related error."""
  pass


class TimezoneNotSpecifiedError(TimestampError):
  """This error is raised when timezone is not specified."""
  pass


class TimeParseError(TimestampError):
  """This error is raised when we can't parse the input."""
  pass


# TODO(user): this class needs to handle daylight better


class LocalTimezoneClass(datetime.tzinfo):
  """This class defines local timezone."""

  ZERO = datetime.timedelta(0)
  HOUR = datetime.timedelta(hours=1)

  STDOFFSET = datetime.timedelta(seconds=-time.timezone)
  if time.daylight:
    DSTOFFSET = datetime.timedelta(seconds=-time.altzone)
  else:
    DSTOFFSET = STDOFFSET

  DSTDIFF = DSTOFFSET - STDOFFSET

  def utcoffset(self, dt):
    """datetime -> minutes east of UTC (negative for west of UTC)."""
    if self._isdst(dt):
      return self.DSTOFFSET
    else:
      return self.STDOFFSET

  def dst(self, dt):
    """datetime -> DST offset in minutes east of UTC."""
    if self._isdst(dt):
      return self.DSTDIFF
    else:
      return self.ZERO

  def tzname(self, dt):
    """datetime -> string name of time zone."""
    return time.tzname[self._isdst(dt)]

  def _isdst(self, dt):
    """Return true if given datetime is within local DST."""
    tt = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second,
          dt.weekday(), 0, -1)
    stamp = time.mktime(tt)
    tt = time.localtime(stamp)
    return tt.tm_isdst > 0

  def __repr__(self):
    """Return string '<Local>'."""
    return '<Local>'

  def localize(self, dt, unused_is_dst=False):
    """Convert naive time to local time."""
    if dt.tzinfo is not None:
      raise ValueError('Not naive datetime (tzinfo is already set)')
    return dt.replace(tzinfo=self)

  def normalize(self, dt, unused_is_dst=False):
    """Correct the timezone information on the given datetime."""
    if dt.tzinfo is None:
      raise ValueError('Naive time - no tzinfo set')
    return dt.replace(tzinfo=self)


LocalTimezone = LocalTimezoneClass()


class BaseTimestamp(datetime.datetime):
  """Our kind of wrapper over datetime.datetime.

  The objects produced by methods now, today, fromtimestamp, utcnow,
  utcfromtimestamp are timezone-aware (with correct timezone).
  We also overload __add__ and __sub__ method, to fix the result of arithmetic
  operations.
  """

  LocalTimezone = LocalTimezone

  @classmethod
  def AddLocalTimezone(cls, obj):
    """If obj is naive, add local timezone to it."""
    if not obj.tzinfo:
      return obj.replace(tzinfo=cls.LocalTimezone)
    return obj

  @classmethod
  def Localize(cls, obj):
    """If obj is naive, localize it to cls.LocalTimezone."""
    if not obj.tzinfo:
      return cls.LocalTimezone.localize(obj)
    return obj

  def __add__(self, *args, **kwargs):
    """x.__add__(y) <==> x+y."""
    r = super(BaseTimestamp, self).__add__(*args, **kwargs)
    return type(self)(r.year, r.month, r.day, r.hour, r.minute, r.second,
                      r.microsecond, r.tzinfo)

  def __sub__(self, *args, **kwargs):
    """x.__add__(y) <==> x-y."""
    r = super(BaseTimestamp, self).__sub__(*args, **kwargs)
    if isinstance(r, datetime.datetime):
      return type(self)(r.year, r.month, r.day, r.hour, r.minute, r.second,
                        r.microsecond, r.tzinfo)
    return r

  @classmethod
  def now(cls, *args, **kwargs):
    """Get a timestamp corresponding to right now.

    Args:
      args: Positional arguments to pass to datetime.datetime.now().
      kwargs: Keyword arguments to pass to datetime.datetime.now(). If tz is not
              specified, local timezone is assumed.

    Returns:
      A new BaseTimestamp with tz's local day and time.
    """
    return cls.AddLocalTimezone(
        super(BaseTimestamp, cls).now(*args, **kwargs))

  @classmethod
  def today(cls):
    """Current BaseTimestamp.

    Same as self.__class__.fromtimestamp(time.time()).
    Returns:
      New self.__class__.
    """
    return cls.AddLocalTimezone(super(BaseTimestamp, cls).today())

  @classmethod
  def fromtimestamp(cls, *args, **kwargs):
    """Get a new localized timestamp from a POSIX timestamp.

    Args:
      args: Positional arguments to pass to datetime.datetime.fromtimestamp().
      kwargs: Keyword arguments to pass to datetime.datetime.fromtimestamp().
              If tz is not specified, local timezone is assumed.

    Returns:
      A new BaseTimestamp with tz's local day and time.
    """
    return cls.Localize(
        super(BaseTimestamp, cls).fromtimestamp(*args, **kwargs))

  @classmethod
  def utcnow(cls):
    """Return a new BaseTimestamp representing UTC day and time."""
    return super(BaseTimestamp, cls).utcnow().replace(tzinfo=pytz.utc)

  @classmethod
  def utcfromtimestamp(cls, *args, **kwargs):
    """timestamp -> UTC datetime from a POSIX timestamp (like time.time())."""
    return super(BaseTimestamp, cls).utcfromtimestamp(
        *args, **kwargs).replace(tzinfo=pytz.utc)

  @classmethod
  def strptime(cls, date_string, format, tz=None):
    """Parse date_string according to format and construct BaseTimestamp.

    Args:
      date_string: string passed to time.strptime.
      format: format string passed to time.strptime.
      tz: if not specified, local timezone assumed.
    Returns:
      New BaseTimestamp.
    """
    if tz is None:
      return cls.Localize(cls(*(time.strptime(date_string, format)[:6])))
    return tz.localize(cls(*(time.strptime(date_string, format)[:6])))

  def astimezone(self, *args, **kwargs):
    """tz -> convert to time in new timezone tz."""
    r = super(BaseTimestamp, self).astimezone(*args, **kwargs)
    return type(self)(r.year, r.month, r.day, r.hour, r.minute, r.second,
                      r.microsecond, r.tzinfo)

  @classmethod
  def FromMicroTimestamp(cls, ts):
    """Create new Timestamp object from microsecond UTC timestamp value.

    Args:
      ts: integer microsecond UTC timestamp
    Returns:
      New cls()
    """
    return cls.utcfromtimestamp(ts/_MICROSECONDS_PER_SECOND_F)

  def AsSecondsSinceEpoch(self):
    """Return number of seconds since epoch (timestamp in seconds)."""
    return GetSecondsSinceEpoch(self.utctimetuple())

  def AsMicroTimestamp(self):
    """Return microsecond timestamp constructed from this object."""
    return (SecondsToMicroseconds(self.AsSecondsSinceEpoch()) +
            self.microsecond)

  @classmethod
  def combine(cls, datepart, timepart, tz=None):
    """Combine date and time into timestamp, timezone-aware.

    Args:
      datepart: datetime.date
      timepart: datetime.time
      tz: timezone or None
    Returns:
      timestamp object
    """
    result = super(BaseTimestamp, cls).combine(datepart, timepart)
    if tz:
      result = tz.localize(result)
    return result


class Timestamp(BaseTimestamp):
  """This subclass contains methods to parse W3C and interval date spec.

  The interval date specification is in the form "1D", where "D" can be
  "s"econds "m"inutes "h"ours "D"ays "W"eeks "M"onths "Y"ears.
  """
  INTERVAL_CONV_DICT = {'s': 1, 'm': 60, 'h': 3600, 'D': 86400,
                        'W': 7*86400, 'M': 30*86400, 'Y': 365*86400}
  INTERVAL_REGEXP = re.compile('^([0-9]+)([smhDWMY])')

  @classmethod
  def _StringToTime(cls, timestring, tz=None):
    """Use dateutil.parser to convert string into timestamp.

    dateutil.parser understands ISO8601 which is really handy.

    Args:
      timestring: string with datetime
      tz: optional timezone, if timezone is omitted from timestring.
    Returns:
      New Timestamp.
    """

    def _TimezoneWrapper(tzname, tzoffset):
      if tzname:
        return pytz.timezone(tzname)
      if tzoffset is not None:
        return pytz.FixedOffset(int(tzoffset / 60))
      return tz or cls.LocalTimezone

    r = parser.parse(timestring, tzinfos=_TimezoneWrapper)
    result = cls(r.year, r.month, r.day, r.hour, r.minute, r.second,
                 r.microsecond, r.tzinfo)

    return result

  @classmethod
  def _IntStringToInterval(cls, timestring):
    """Parse interval date specification and create a timedelta object."""
    total = 0
    while timestring:
      match = cls.INTERVAL_REGEXP.match(timestring)

      if not match: return
      num, ext = int(match.group(1)), match.group(2)
      if not ext in cls.INTERVAL_CONV_DICT or num < 0: return
      total += num * cls.INTERVAL_CONV_DICT[ext]
      timestring = timestring[match.end(0):]
    return datetime.timedelta(seconds=total)

  @classmethod
  def FromString(cls, value, tz=None):
    """Try to create a Timestamp from a string."""
    val = cls._StringToTime(value, tz)
    if val:
      return val

    val = cls._IntStringToInterval(value)
    if val:
      return cls.utcnow() - val

    raise TimeParseError(value)


# What's written below is a clear python bug. I mean, okay, I can apply
# negative timezone to it and end result will be inconversible.

MAXIMUM_PYTHON_TIMESTAMP = Timestamp(
    9999, 12, 31, 23, 59, 59, 999999, UTC)

# This is also a bug. It is called 32bit time_t. I hate it.
# This is fixed in 2.5, btw.

MAXIMUM_MICROSECOND_TIMESTAMP = 0x80000000 * _MICROSECONDS_PER_SECOND - 1
MAXIMUM_MICROSECOND_TIMESTAMP_AS_TS = Timestamp(2038, 1, 19, 3, 14, 7, 999999)
