#!/usr/bin/env python
#
# Copyright 2007 Google Inc. All Rights Reserved.
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

"""Test tool to demonstrate appcommands.py usage.

This tool shows how to use appcommands.py.
"""



from google.apputils import appcommands
import gflags as flags

FLAGS = flags.FLAGS

flags.DEFINE_string('hint', '', 'Global hint to show in commands')


# Name taken from app.py
class Test1(appcommands.Cmd):
  """Help for test1."""

  def __init__(self, name, flag_values, **kargs):
    """Init and register flags specific to command."""
    appcommands.Cmd.__init__(self, name, flag_values=flag_values, **kargs)
    # self._all_commands_help allows you to define a different message to be
    # displayed when all commands are displayed vs. the single command.
    self._all_commands_help = ''
    # Flag --fail1 is specific to this command
    flags.DEFINE_boolean('fail1', False, 'Make test1 fail',
                         flag_values=flag_values)
    flags.DEFINE_string('foo', '', 'Param foo', flag_values=flag_values)
    flags.DEFINE_string('bar', '', 'Param bar', flag_values=flag_values)
    flags.DEFINE_integer('intfoo', 0, 'Integer foo', flag_values=flag_values)

  def Run(self, argv):
    """Output 'Command1' and flag info.

    Args:
      argv: Remaining command line arguments after parsing flags and command

    Returns:
      Value of flag fail1
    """
    print 'Command1'
    if FLAGS.hint:
      print "Hint1:'%s'" % FLAGS.hint
    print "Foo1:'%s'" % FLAGS.foo
    print "Bar1:'%s'" % FLAGS.bar
    return FLAGS.fail1 * 1


class Test2(appcommands.Cmd):
  """Help for test2."""

  def __init__(self, name, flag_values):
    """Init and register flags specific to command."""
    appcommands.Cmd.__init__(self, name, flag_values)
    flags.DEFINE_boolean('fail2', False, 'Make test2 fail',
                         flag_values=flag_values)
    flags.DEFINE_string('foo', '', 'Param foo', flag_values=flag_values)
    flags.DEFINE_string('bar', '', 'Param bar', flag_values=flag_values)

  def Run(self, argv):
    """Output 'Command2' and flag info.

    Args:
      argv: Remaining command line arguments after parsing flags and command

    Returns:
      Value of flag fail2
    """
    print 'Command2'
    if FLAGS.hint:
      print "Hint2:'%s'" % FLAGS.hint
    print "Foo2:'%s'" % FLAGS.foo
    print "Bar2:'%s'" % FLAGS.bar
    return FLAGS.fail2 * 1


def Test3(unused_argv):
  """Help for test3."""
  print 'Command3'


def Test4(unused_argv):
  """Help for test4."""
  print 'Command4'


def main(unused_argv):
  """Register the commands."""
  appcommands.AddCmd('test1', Test1, command_aliases=['testalias1',
                                                      'testalias2'])
  appcommands.AddCmd('test2', Test2)
  appcommands.AddCmdFunc('test3', Test3)
  appcommands.AddCmdFunc('test4', Test4, command_aliases=['testalias3'],
                         all_commands_help='')


if __name__ == '__main__':
  appcommands.Run()
