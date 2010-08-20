#!/usr/bin/env python
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

"""This module is the base for programs that provide multiple commands.

This provides command line tools that have a few shared global flags
followed by a command name followed by command specific flags and
arguments. That is:
  tool [--global_flags] command [--command_flags] [args]

The module is built on top of app.py and 'overrides' a bit of it. Yet
the interface is mostly the same. The main difference is that your main
is supposed to register commands and return without further execution
of the commands. Though pre checking is of course welcome. Also your
global initialization should call appcommands.Run() rather than app.run().

To register commands use AddCmd() or AddCmdFunc(). Where the former is used
for commands that derive from class Cmd and the latter is used to wrap simple
functions.

This module itself registers the command 'help' that allows to retrieve help
for all or specific commands.

Example:

<code>
from mx import DateTime


class CmdDate(appcommands.Cmd):
  \"\"\"This docstring contains the help for the date command.\"\"\"

  def Run(self, argv):
    print DateTime.now()


def main(argv):
  appcommands.AddCmd('date', CmdDate)


if __name__ == '__main__':
  appcommands.Run()
</code>

In the above example the name of the registered command on the command line is
'date'. Thus, to get the date you would execute:
  tool date
To get a list of available commands run:
  tool help
For help with a specific command, you would execute:
  tool help date
For help on flags run one of the following:
  tool --help
Note that 'tool --help' gives you information on global flags, just like for
applications that do not use appcommand. Likewise 'tool --helpshort' and the
other help-flags from app.py are also available.

The above example also demonstrates that you only have to call
  appcommands.Run()
and register your commands in main() to initialize your program with appcommands
(and app).

Handling of flags:
  Flags can be registered just as with any other google tool using flags.py.
  But you can also provide command specific flags. To do so simply add a
  flags registering code into the __init__ function of your Cmd classes passing
  parameter flag_values to any flags registering calls. These flags will get
  copied to the global flag list so that once the command is detected they
  behave just like any other flag. That means these flags won't be available
  for other commands. Note that it is possible to register flags with more
  than one command.

Getting help:
  This module activates formatting and wrapping to help output. That is the
  main difference to help created from app.py. So just as app.py appcommands.py
  will create help from the main modules main __doc__. But it adds the new
  'help' command that allows to get a list of all available commands.
  Each commands help will be followed by the registered command specific flags
  along with their defaults and help. After help for all commands there will
  also be a list of all registered global flags with their defaults and help.

  The text for the commands help can best be supplied by overwriting the
  __doc__ property of the Cmd classes for commands registered with AddCmd() or
  the __doc__ property of command functions registered AddCmdFunc().

Inner working:
  This module interacts with app.py by replacing its inner start dispatcher.
  The replacement version basically does the same, registering help flags,
  checking whether help falgs were present and calling the main modules main
  function. However unlike app.py, this module epxpects main() to only register
  commands and then to return. After having all commands registered
  appcommands.py will then parse the remaining arguments for any registered
  command. If one is found it will get executed. Otherwise a short usage info
  will be displayed.

  Each provided command must be an instance of Cmd. If commands get registered
  from global functions using AddCmdFunc() then the helper class _FunctionalCmd
  will be used in the registering process.
"""



import os
import pdb
import sys

from google.apputils import app
import gflags as flags

FLAGS = flags.FLAGS


# module exceptions:
class AppCommandsError(Exception):
  """The base class for all flags errors."""
  pass


_cmd_argv = None        # remaning arguments with index 0 = sys.argv[0]
_cmd_list = {}          # list of commands index by name (_Cmd instances)


def GetAppBasename():
  """Returns the friendly basename of this application."""
  return os.path.basename(sys.argv[0])


def ShortHelpAndExit(message=None):
  """Display optional message followed by a note on how to get help then exit.

  Args:
    message: optional message to display
  """
  sys.stdout.flush()
  if message is not None:
    sys.stderr.write('%s\n' % message)
  sys.stderr.write("Run '%s help' to get help\n" % GetAppBasename())
  sys.exit(1)


def GetCommandList():
  """Return list of registered commands."""
  # pylint: disable-msg=W0602
  global _cmd_list
  return _cmd_list


def GetCommandByName(name):
  """Get the command or None if name is not a registered command.

  Args:
    name:  name of command to look for

  Returns:
    Cmd instance holding the command or None
  """
  return GetCommandList().get(name)


def GetCommandArgv():
  """Return list of remaining args."""
  return _cmd_argv


def GetMaxCommandLength():
  """Returns the length of the longest registered command."""
  return max([len(cmd_name) for cmd_name in GetCommandList()])


class Cmd(object):
  """Abstract class describing and implementing a command.

  When creating code for a command, at least you have to derive this class
  and override method Run(). The other methods of this class might be
  overridden as well. Check their documentation for details. If the the command
  need any specific flags, use __init__ for registration.
  """

  def __init__(self, name, flag_values):
    """Initialize and check whether self is actually a Cmd instance.

    This can be used to register command specific flags. If you do so
    remember that you have to provide the 'flag_values=flag_values'
    parameter to any flags.DEFINE_*() call.

    Args:
      name:        Nameof command
      flag_values: FlagValues() instance that needs to be passed as flag_values
                   parameter to any flags registering call.
    Raises:
      AppCommandsError: if self is Cmd (Cmd is abstract)
    """
    self._command_name = name
    self._command_flags = flag_values
    if type(self) is Cmd:
      raise AppCommandsError('Cmd is abstract and cannot be instantiated')

  def Run(self, argv):
    """Execute the command. Must be provided by the implementing class.

    Args:
      argv: Remaining command line arguemnts after parsing flags and command
            (that is a copy of sys.argv at the time of the function call with
            all parsed flags removed).

    Returns:
      0 for success, anything else for failure (must return with integer).
      Alternatively you may return None (or not use a return statement at all).

    Raises:
      AppCommandsError: Always as in must be overwitten
    """
    raise AppCommandsError(type(self) + '.Run() is not implemented')

  def CommandRun(self, argv):
    """Execute the command with given arguments.

    First register and parse additional flags. Then run the command.

    Returns:
      Command return value.

    Args:
      argv: Remaining command line arguments after parsing command and flags
            (that is a copy of sys.argv at the time of the function call with
            all parsed flags removed).
    """
    # Register flags global when run normally
    FLAGS.AppendFlagValues(self._command_flags)
    # Prepare flags parsing, to redirect help, to show help for command
    orig_app_usage = app.usage

    def ReplacementAppUsage(shorthelp=0, writeto_stdout=1, detailed_error=None,
                            exitcode=None):
      AppcommandsUsage(shorthelp, writeto_stdout, detailed_error, exitcode=1,
                       show_cmd=self._command_name, show_global_flags=True)
    app.usage = ReplacementAppUsage
    # Parse flags and restore app.usage afterwards
    try:
      try:
        argv = ParseFlagsWithUsage(argv)
        # Run command
        if FLAGS.run_with_pdb:
          ret = pdb.runcall(self.Run, argv)
        else:
          ret = self.Run(argv)
        if ret is None:
          ret = 0
        else:
          assert isinstance(ret, int)
        return ret
      except app.UsageError, error:
        app.usage(shorthelp=1, detailed_error=error, exitcode=error.exitcode)
    finally:
      # Restore app.usage and remove this command's flags from the global flags.
      app.usage = orig_app_usage
      for flag_name in self._command_flags.FlagDict():
        delattr(FLAGS, flag_name)

  def CommandGetHelp(self, unused_argv):
    """Get help string for command.

    Args:
      argv: Remaining command line flags and arguemnts after parsing command
            (that is a copy of sys.argv at the time of the function call with
            all parsed flags removed); unused in this default implementation,
            but may be used in subclasses.

    Returns:
      Help string, one of the following (by order):
        - Result of the registered 'help' function (if any)
        - Doc string of the Cmd class (if any)
        - Default fallback string
    """
    if self.__doc__:
      return flags.DocToHelp(self.__doc__)
    else:
      return 'No help available'


class _FunctionalCmd(Cmd):
  """Class to wrap functions as CMD instances.

  Args:
    cmd_func:   command function
  """

  def __init__(self, name, flag_values, cmd_func):
    """Create a functional command.

    Args:
      name:        Name of command
      flag_values: FlagValues() instance that needs to be passed as flag_values
                   parameter to any flags registering call.
      cmd_func:    Function to call when command is to be executed.
    """
    Cmd.__init__(self, name, flag_values)
    self._cmd_func = cmd_func

  def CommandGetHelp(self, unused_argv):
    """Get help for command.

    Args:
      argv: Remaining command line flags and arguemnts after parsing command
            (that is a copy of sys.argv at the time of the function call with
            all parsed flags removed); unused in this implementation.

    Returns:
      __doc__ property for command function or a message stating there is no
      help.
    """
    if self._cmd_func.__doc__ is not None:
      return flags.DocToHelp(self._cmd_func.__doc__)
    else:
      return 'No help available'

  def Run(self, argv):
    """Execute the command with given arguments.

    Args:
      argv: Remaining command line flags and arguemnts after parsing command
            (that is a copy of sys.argv at the time of the function call with
            all parsed flags removed).

    Returns:
      Command return value.
    """
    return self._cmd_func(argv)


def _AddCmdInstance(command_name, cmd):
  """Add a command from a Cmd instance.

  Args:
    command_name: name of the command which will be used in argument parsing
    cmd:          Cmd instance to register

  Raises:
    AppCommandsError: is command is already registered OR cmd is not a subclass
                      of Cmd
    AppCommandsError: if name is already registered OR name is not a string OR
                      name is too short OR name does not start with a letter OR
                      name contains any non alphanumeric characters besides
                      '_'.
  """
  # Update global command list.
  # pylint: disable-msg=W0602
  global _cmd_list
  if not issubclass(cmd.__class__, Cmd):
    raise AppCommandsError('Command must be an instance of commands.Cmd')
  # Only allow strings (reject unicode as well)
  if not isinstance(command_name, str) or len(command_name) <= 1:
    raise AppCommandsError("Command '%s' not a string or too short"
                           % str(command_name))
  if not command_name[0].isalpha():
    raise AppCommandsError("Command '%s' does not start with a letter"
                           % command_name)
  if [c for c in command_name if not (c.isalnum() or c == '_')]:
    raise AppCommandsError("Command '%s' contains non alphanumeric characters"
                           % command_name)
  if command_name in GetCommandList():
    raise AppCommandsError("Command '%s' already defined" % command_name)
  _cmd_list[command_name] = cmd


def AddCmd(command_name, cmd_class):
  """Add a command from a Cmd subclass.

  Args:
    command_name: name of the command which will be used in argument parsing
    cmd_class:    A class derived from Cmd that holds the command to register

  Raises:
    AppCommandsError: if cmd_class is not a subclass of Cmd
  """
  if not issubclass(cmd_class, Cmd):
    raise AppCommandsError('Command must be an instance of commands.Cmd')
  _AddCmdInstance(command_name, cmd_class(command_name, flags.FlagValues()))


def AddCmdFunc(command_name, cmd_func):
  """Add a new command to the list of registered commands.

  Args:
    command_name: name of the command which will be used in argument parsing
    cmd_func:     command function, this function received the remaining
                  arguments as its only parameter. It is supposed to do the
                  command work and then return with the command result that is
                  being used as the shell exit code.
  """
  _AddCmdInstance(command_name,
                  _FunctionalCmd(command_name, flags.FlagValues(), cmd_func))


class _CmdHelp(Cmd):
  """Standard help command.

  Allows to provide help for all or specific commands.
  """

  def Run(self, argv):
    """Execute help command.

    If an argument is given and that argument is a registered command name,
    help specific to that command is being displayed. If the command is unknown
    a fatal error will be displayed. If no argument is present then help for
    all commands will be presented.

    If a specific command help is being generated, the list of commands is
    temporarily replaced with one containing only that command. Thus the call
    to usage() will only show help for that command. Otherwise call usage()
    will show help for all registered commands as it sees all commands.

    Args:
      argv: Remaining command line flags and arguemnts after parsing command
            (that is a copy of sys.argv at the time of the function call with
            all parsed flags removed).
            So argv[0] is the program and argv[1] will be the first argument to
            the call. For instance 'tool.py help command' will result in argv
            containing ('tool.py', 'command'). In this case the list of
            commands is searched for 'command'.

    Returns:
      1 for failure
    """
    if len(argv) > 1 and argv[1] in GetCommandList():
      show_cmd = argv[1]
    else:
      show_cmd = None
    AppcommandsUsage(shorthelp=0, writeto_stdout=1, detailed_error=None,
                     exitcode=1, show_cmd=show_cmd, show_global_flags=False)

  def CommandGetHelp(self, unused_argv):
    """Returns: Help for command."""
    cmd_help = ('Help for all or selected command:\n'
                '\t%(prog)s help [<command>]\n\n'
                'To retrieve help with global flags:\n'
                '\t%(prog)s --help\n\n'
                'To retrieve help with flags only from the main module:\n'
                '\t%(prog)s --helpshort [<command>]\n\n'
                % {'prog': GetAppBasename()})
    return flags.DocToHelp(cmd_help)


def GetSynopsis():
  """Get synopsis for program.

  Returns:
    Synopsis including program basename.
  """
  return '%s [--global_flags] <command> [--command_flags] [args]' % (
      GetAppBasename())


def _UsageFooter(detailed_error, cmd_names):
  """Output a footer at the end of usage or help output.

  Args:
    detailed_error: additional detail about why usage info was presented.
    cmd_names:      list of command names for which help was shown or None.
  Returns:
    Generated footer that contains 'Run..' messages if appropriate.
  """
  footer = []
  if not cmd_names or len(cmd_names) == 1:
    footer.append("Run '%s help' to see the list of available commands."
                  % GetAppBasename())
  if not cmd_names or len(cmd_names) == len(GetCommandList()):
    footer.append("Run '%s help <command>' to get help for <command>."
                  % GetAppBasename())
  if detailed_error is not None:
    if footer:
      footer.append('')
    footer.append('%s' % detailed_error)
  return '\n'.join(footer)


def AppcommandsUsage(shorthelp=0, writeto_stdout=0, detailed_error=None,
                     exitcode=None, show_cmd=None, show_global_flags=False):
  """Output usage or help information.

  Extracts the __doc__ string from the __main__ module and writes it to
  stderr. If that string contains a '%s' then that is replaced by the command
  pathname. Otherwise a default usgae string is being generated.

  The output varies depending on the following:
  - FLAGS.help
  - FLAGS.helpshort
  - show_cmd
  - show_global_flags

  Args:
    shorthelp:      print only command and main module flags, rather than all.
    writeto_stdout: write help message to stdout, rather than to stderr.
    detailed_error: additional detail about why usage info was presented.
    exitcode:       if set, exit with this status code after writing help.
    show_cmd:       show help for this command only (name of command).
    show_global_flags: show help for global flags.
  """
  if writeto_stdout:
    stdfile = sys.stdout
  else:
    stdfile = sys.stderr

  prefix = ''.rjust(GetMaxCommandLength() + 2)
  # Deal with header, containing general tool documentation
  doc = sys.modules['__main__'].__doc__
  if doc:
    help_msg = flags.DocToHelp(doc.replace('%s', sys.argv[0]))
    stdfile.write(flags.TextWrap(help_msg, flags.GetHelpWidth()))
    stdfile.write('\n\n\n')
  if not doc or doc.find('%s') == -1:
    synopsis = 'USAGE: ' + GetSynopsis()
    stdfile.write(flags.TextWrap(synopsis, flags.GetHelpWidth(), '       ',
                                 ''))
    stdfile.write('\n\n\n')
  # Special case just 'help' registered, that means run as 'tool --help'.
  if len(GetCommandList()) == 1:
    cmd_names = []
  else:
    # Show list of commands
    if show_cmd is None or show_cmd == 'help':
      cmd_names = GetCommandList().keys()
      cmd_names.sort()
      stdfile.write('Any of the following commands:\n')
      doc = ', '.join(cmd_names)
      stdfile.write(flags.TextWrap(doc, flags.GetHelpWidth(), '  '))
      stdfile.write('\n\n\n')
    # Prepare list of commands to show help for
    if show_cmd is not None:
      cmd_names = [show_cmd]  # show only one command
    elif FLAGS.help or FLAGS.helpshort or shorthelp:
      cmd_names = []
    else:
      cmd_names = GetCommandList().keys()  # show all commands
      cmd_names.sort()
  # Show the command help (none, one specific, or all)
  for name in cmd_names:
    command = GetCommandByName(name)
    prefix1 = '%-*s ' % (GetMaxCommandLength()+1, name)
    cmd_help = command.CommandGetHelp(GetCommandArgv()).strip()
    stdfile.write(flags.TextWrap(cmd_help, flags.GetHelpWidth(), prefix,
                                 prefix1))
    stdfile.write('\n\n')
    # When showing help for exactly one command we show its flags
    if len(cmd_names) == 1:
      # Need to register flags for command prior to be able to use them.
      # We do not register them globally so that they do not reappear.
      # pylint: disable-msg=W0212
      cmd_flags = command._command_flags
      if cmd_flags.RegisteredFlags():
        stdfile.write('%sFlags for %s:\n' % (prefix, name))
        stdfile.write(cmd_flags.GetHelp(prefix+'  '))
        stdfile.write('\n\n')
  stdfile.write('\n')
  # Now show global flags as asked for
  if show_global_flags:
    stdfile.write('Global flags:\n')
    if shorthelp:
      stdfile.write(FLAGS.MainModuleHelp())
    else:
      stdfile.write(FLAGS.GetHelp())
    stdfile.write('\n')
  else:
    stdfile.write("Run '%s --help' to get help for global flags."
                  % GetAppBasename())
  stdfile.write('\n%s\n' % _UsageFooter(detailed_error, cmd_names))
  if exitcode is not None:
    sys.exit(exitcode)


def ParseFlagsWithUsage(argv):
  """Parse the flags, exiting (after printing usage) if they are unparseable.

  Args:
    argv: command line arguments

  Returns:
    remaining command line arguments after parsing flags
  """
  # Update the global commands.
  # pylint: disable-msg=W0603
  global _cmd_argv
  try:
    _cmd_argv = FLAGS(argv)
    return _cmd_argv
  except flags.FlagsError, error:
    ShortHelpAndExit('FATAL Flags parsing error: %s' % error)


def GetCommand(command_required):
  """Get the command or return None (or issue an error) if there is none.

  Args:
    command_required: whether to issue an error if no command is present

  Returns:
    command or None, if command_required is True then return value is a valid
    command or the program will exit. The program also exits if a comamnd was
    specified but that command does not exist.
  """
  # Update the global commands.
  # pylint: disable-msg=W0603
  global _cmd_argv
  _cmd_argv = ParseFlagsWithUsage(_cmd_argv)
  if len(_cmd_argv) < 2:
    if command_required:
      ShortHelpAndExit('FATAL Command expectd but none given')
    return None
  command = GetCommandByName(_cmd_argv[1])
  if command is None:
    ShortHelpAndExit("FATAL Command '%s' unknown" % _cmd_argv[1])
  del _cmd_argv[1]
  return command


def _CommandsStart():
  """Main initialization.

  This initializes flag values, and calls __main__.main().  Only non-flag
  arguments are passed to main().  The return value of main() is used as the
  exit status.

  """
  app.RegisterAndParseFlagsWithUsage()
  # The following is supposed to return after registering additional commands
  try:
    sys.modules['__main__'].main(GetCommandArgv())
  # If sys.exit was called, return with error code.
  except SystemExit, e:
    sys.exit(e.code)
  except Exception, error:
    ShortHelpAndExit('FATAL error in main: %s' % error)

  if len(GetCommandArgv()) > 1:
    command = GetCommand(command_required=True)
  else:
    command = GetCommandByName('help')
  sys.exit(command.CommandRun(GetCommandArgv()))


def Run():
  """This must be called from __main__ modules main, instead of app.run().

  app.run will base its actions on its stacktrace.

  Returns:
    app.run()
  """
  return app.run()


# Always register 'help' command
AddCmd('help', _CmdHelp)
app.parse_flags_with_usage = ParseFlagsWithUsage
app.really_start = _CommandsStart


def _ReplacementAppUsage(shorthelp=0, writeto_stdout=0, detailed_error=None,
                         exitcode=None):
  AppcommandsUsage(shorthelp, writeto_stdout, detailed_error, exitcode=exitcode,
                   show_cmd=None, show_global_flags=True)

app.usage = _ReplacementAppUsage

if __name__ == '__main__':
  Run()
