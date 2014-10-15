#! /bin/bash
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
#
# Author: mboerger@google.com

PYTHON=$(which python)
function die {
	echo "$1"
	exit 1
}

IMPORTS="from google.apputils import app
from google.apputils import appcommands
import gflags as flags"

# This should exit with error code because no main defined
$PYTHON -c "${IMPORTS}
appcommands.Run()" >/dev/null 2>&1 && \
    die "Test 1 failed"

# Standard use. This should exit successfully
$PYTHON -c "${IMPORTS}
import sys
def test(argv):
  return 0
def main(argv):
  appcommands.AddCmdFunc('test', test)
appcommands.Run()
sys.exit(1)" test || \
    die "Test 2 failed"

# Even with no return from Cmds Run() does not return
$PYTHON -c "${IMPORTS}
import sys
def test(argv):
  return
def main(argv):
  appcommands.AddCmdFunc('test', test)
appcommands.Run()
sys.exit(1)" test || \
    die "Test 3 failed"

# Standard use with returning an error code.
$PYTHON -c "${IMPORTS}
import sys
def test(argv):
  return 1
def main(argv):
  appcommands.AddCmdFunc('test', test)
appcommands.Run()
sys.exit(0)" test && \
    die "Test 4 failed"

# Executing two commands in single mode does not work (execute only first)
$PYTHON -c "${IMPORTS}
def test1(argv):
  return 0
def test2(argv):
  return 1
def main(argv):
  appcommands.AddCmdFunc('test1', test1)
  appcommands.AddCmdFunc('test2', test2)
appcommands.Run()" test1 test2 || \
    die "Test 5 failed"

# Registering a command twice does not work.
$PYTHON -c "${IMPORTS}
def test1(argv):
  return 0
def main(argv):
  appcommands.AddCmdFunc('test', test1)
  appcommands.AddCmdFunc('test', test1)
appcommands.Run()" test >/dev/null 2>&1 && \
    die "Test 6 failed"

# Executing help, returns non zero return code (1), then check result
RES=`$PYTHON -c "${IMPORTS}
def test1(argv):
  '''Help1'''
  return 0
def test2(argv):
  '''Help2'''
  return 0
def main(argv):
  appcommands.AddCmdFunc('test1', test1)
  appcommands.AddCmdFunc('test2', test2)
appcommands.Run()" help` && die "Test 7 failed"

echo "${RES}" | grep -q "USAGE: " || die "Test 8 failed"
echo "${RES}" | sed -ne '/following commands:/,/.*/p' | \
    grep -q "help, test1, test2" || die "Test 9 failed"
echo "${RES}" | grep -q -E "(^| )test1[ \t]+Help1($| )" || die "Test 10 failed"
echo "${RES}" | grep -q -E "(^| )test2[ \t]+Help2($| )" || die "Test 11 failed"

# Executing help for command, returns non zero return code (1), then check result
RES=`$PYTHON -c "${IMPORTS}
def test1(argv):
  '''Help1'''
  return 0
def test2(argv):
  '''Help2'''
  return 0
def main(argv):
  appcommands.AddCmdFunc('test1', test1)
  appcommands.AddCmdFunc('test2', test2)
appcommands.Run()" help test2` && die "Test 12 failed"

echo "${RES}" | grep -q "USAGE: " || die "Test 13 failed"
echo "${RES}" | grep -q -E "(^| )Any of the following commands:" && die "Test 14 failed"
echo "${RES}" | grep -q -E "(^| )test1[ \t]+" && die "Test 15 failed"
echo "${RES}" | grep -q -E "(^| )test2[ \t]+Help2($| )" || die "Test 16 failed"

# Returning False succeeds
$PYTHON -c "${IMPORTS}
def test(argv): return False
def main(argv):
  appcommands.AddCmdFunc('test', test)
appcommands.Run()" test || die "Test 17 failed"

# Returning True fails
$PYTHON -c "${IMPORTS}
def test(argv): return True
def main(argv):
  appcommands.AddCmdFunc('test', test)
appcommands.Run()" test && die "Test 18 failed"

# Registering using AddCmd instead of AddCmdFunc, should be the normal case
$PYTHON -c "${IMPORTS}
class test(appcommands.Cmd):
  def Run(self, argv): return 0
def main(argv):
  appcommands.AddCmd('test', test)
appcommands.Run()" test || die "Test 19 failed"

# Registering using AddCmd instead of AddCmdFunc, now fail
$PYTHON -c "${IMPORTS}
class test(appcommands.Cmd):
  def Run(self, argv): return 1
def main(argv):
  appcommands.AddCmd('test', test)
appcommands.Run()" test && die "Test 20 failed"

TEST=./appcommands_example.py

if test -s "${TEST}.py"; then
  TEST="${TEST}.py"
elif test ! -s "${TEST}"; then
  die "Could not locate ${TEST}"
fi

# Success
$PYTHON $TEST test1 >/dev/null 2>&1 || die "Test 21 failed"
$PYTHON $TEST test1|grep -q 'Command1' 2>&1 || die "Test 22 failed"
$PYTHON $TEST test2|grep -q 'Command2' 2>&1 || die "Test 23 failed"
$PYTHON $TEST test3|grep -q 'Command3' 2>&1 || die "Test 24 failed"

# Success, --nofail1 belongs to test1
$PYTHON $TEST test1 --nofail1 >/dev/null 2>&1 || die "Test 25 failed"

# Failure, --fail1
$PYTHON $TEST test1 --fail1 >/dev/null 2>&1 && die "Test 26 failed"

# Failure, --nofail1 does not belong to test2
$PYTHON $TEST test2 --nofail1 >/dev/null 2>&1 && die "Test 27 failed"

# Failure, --nofail1 must appear after its command
$PYTHON $TEST --nofail1 test1 >/dev/null 2>&1 && die "Test 28 failed"

# Failure, explicit from --fail2
$PYTHON $TEST test2 --fail2 >/dev/null 2>&1 && die "Test 29 failed"

# Success, --hint before command, foo shown with test1
$PYTHON $TEST --hint 'XYZ' test1|grep -q "Hint1:'XYZ'" || die "Test 30 failed"

# Success, --hint before command, foo shown with test1
$PYTHON $TEST test1 --hint 'XYZ'|grep -q "Hint1:'XYZ'" || die "Test 31 failed"

# Success, test1b --allhelp, modified _all_commands_help shown
$PYTHON $TEST test1b --allhelp|grep -q "AllHelp:'test1b short help'" || die "Test 32 failed"

# Failure, test1 --allhelp, modified _all_commands_help not shown
$PYTHON $TEST test1 --allhelp|grep -q "AllHelp:'test1b short help'" && die "Test 33 failed"

# Test for standard --help
$PYTHON $TEST --help|grep -q "following commands:" && die "Test 34 failed"
$PYTHON $TEST help|grep -q "following commands:" || die "Test 35 failed"

# No help after command
$PYTHON $TEST test1 --help|grep -q "following commands:" && die "Test 36 failed"
$PYTHON $TEST test1 --help 'XYZ'|grep -q "Hint1:'XYZ'" && die "Test 37 failed"

# Help specific to command:
$PYTHON $TEST --help test1|grep -q "following commands:" && die "Test 38 failed"
$PYTHON $TEST --help test1|grep -q "test1 *Help for test1" && die "Test 39 failed"
$PYTHON $TEST help test1|grep -q "following commands:" && die "Test 40 failed"
$PYTHON $TEST help test1|grep -q "test1, testalias1, testalias2" || die\
  "Test 41 failed"
$PYTHON $TEST help testalias1|grep -q "test1, testalias1, testalias2" || die\
  "Test 42 failed"
$PYTHON $TEST help testalias1|grep -q "[-]-foo" || die\
  "Test 43 failed"
$PYTHON $TEST help testalias2|grep -q "[-]-foo" || die\
  "Test 44 failed"
$PYTHON $TEST help test4|grep -q "^ *Help for test4" || die "Test 45 failed"
$PYTHON $TEST help testalias3|grep -q "^ *Help for test4" || die\
  "Test 46 failed"

# Help for cmds with all_command_help.
$PYTHON $TEST help|grep -q "Help for test1. As described by a docstring." || die "Test 47 failed"
$PYTHON $TEST help test1|grep -q "Help for test1. As described by a docstring." || die "Test 48 failed"
$PYTHON $TEST help|grep -q "test1b short help" || die "Test 49 failed"
$PYTHON $TEST help test1b|grep -q "test1b short help" && die "Test 50 failed"
$PYTHON $TEST help|grep -q "is my very favorite test" && die "Test 51 failed"
$PYTHON $TEST help test1b|grep -q "is my very favorite test" || die "Test 52 failed"
$PYTHON $TEST help|grep -q "Help for test4." && die "Test 53 failed"
$PYTHON $TEST help test4|grep -q "Help for test4." || die "Test 54 failed"
$PYTHON $TEST help|grep -q "replacetest4help" || die "Test 55 failed"
$PYTHON $TEST help test4|grep -q "replacetest4help" && die "Test 56 failed"

# Success, --hint before command, foo shown with test1
$PYTHON $TEST --hint 'XYZ' --help|grep -q "following commands:" && die "Test 57 failed"
$PYTHON $TEST --hint 'XYZ' --help|grep -q "XYZ" && die "Test 58 failed"
$PYTHON $TEST --hint 'XYZ' --help|grep -q "This tool shows how" || die "Test 59 failed"
$PYTHON $TEST --hint 'XYZ' help|grep -q "following commands:" || die "Test 60 failed"
$PYTHON $TEST --hint 'XYZ' help|grep -q "XYZ" && die "Test 61 failed"
$PYTHON $TEST --hint 'XYZ' help|grep -q "This tool shows how" || die "Test 62 failed"

# A command name with an letters, numbers, or an underscore is fine
$PYTHON -c "${IMPORTS}
def test(argv):
  return 0
def main(argv):
  appcommands.AddCmdFunc('test', test)
  appcommands.AddCmdFunc('test_foo', test)
  appcommands.AddCmdFunc('a123', test)
appcommands.Run()" test || die "Test 63 failed"

# A command name that starts with a non-alphanumeric characters is not ok
$PYTHON -c "${IMPORTS}
def test(argv):
  return 0
def main(argv):
  appcommands.AddCmdFunc('123', test)
appcommands.Run()" 123 >/dev/null 2>&1 && die "Test 64 failed"

# A command name that contains other characters is not ok
$PYTHON -c "${IMPORTS}
def test(argv):
  return 0
def main(argv):
  appcommands.AddCmdFunc('test+1', test)
appcommands.Run()" "test+1" >/dev/null 2>&1 && die "Test 65 failed"

# If a command raises app.UsageError, usage is printed.
RES=`$PYTHON -c "${IMPORTS}
def test(argv):
  '''Help1'''
  raise app.UsageError('Ha-ha')
def main(argv):
  appcommands.AddCmdFunc('test', test)
appcommands.Run()" test` && die "Test 66 failed"

echo "${RES}" | grep -q "USAGE: " || die "Test 67 failed"
echo "${RES}" | grep -q -E "(^| )test[ \t]+Help1($| )" || die "Test 68 failed"
echo "${RES}" | grep -q -E "(^| )Ha-ha($| )" || die "Test 69 failed"


$PYTHON -c "${IMPORTS}
class Test(appcommands.Cmd):
  def Run(self, argv): return 0
def test(*args, **kwargs):
  return Test(*args, **kwargs)
def main(argv):
  appcommands.AddCmd('test', test)
appcommands.Run()" test || die "Test 73 failed"

# Success, default command set and correctly run.
RES=`$PYTHON -c "${IMPORTS}
class test(appcommands.Cmd):
  def Run(self, argv):
    print 'test running correctly'
    return 0
def main(argv):
  appcommands.AddCmd('test', test)
appcommands.SetDefaultCommand('test')
appcommands.Run()"` || die "Test 74 failed"

echo "${RES}" | grep -q "test running correctly" || die "Test 75 failed"

# Failure, default command set but missing.
$PYTHON -c "${IMPORTS}
class test(appcommands.Cmd):
  def Run(self, argv):
    print 'test running correctly'
    return 0
def main(argv):
  appcommands.AddCmd('test', test)
appcommands.SetDefaultCommand('missing')
appcommands.Run()" >/dev/null 2>&1 && die "Test 76 failed"

echo "PASS"
