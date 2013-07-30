#! /bin/bash
# Copyright 2003 Google Inc. All Rights Reserved.
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
# Author: Douglas Greiman

PYTHON=$(which python)
function die {
	echo "$1"
	exit 1
}

APP_PACKAGE="google.apputils"

# This should exit with error code because no main defined
$PYTHON -c "from ${APP_PACKAGE} import app; app.run()" 2>/dev/null && \
    die "Test 1 failed"

# Standard use. This should exit successfully
$PYTHON -c "from ${APP_PACKAGE} import app
a = 0
def main(argv):
  global a
  a = 1
app.run()
assert a == 1" || \
    die "Test 2 failed"
# app.run called in exec block, script read from -c string. Should succeed.
$PYTHON -c "from ${APP_PACKAGE} import app
a = 0
s='''
def main(argv):
  global a
  a = 1
app.run()
'''
exec s
assert a == 1" || \
    die "Test 4 failed"

# app.run called in exec block, script read from file. Should succeed.
PYFILE=$TEST_TMPDIR/tmp.py
cat >$PYFILE <<EOF
from ${APP_PACKAGE} import app
a = 0
s='''
def main(argv):
  global a
  a = 1
app.run()
'''
exec s
assert a == 1
EOF

$PYTHON $PYFILE || \
    die "Test 5 failed"
rm -f $PYFILE
# Test for usage from --help
$PYTHON -c "from ${APP_PACKAGE} import app
def main(argv):
  pass
app.run()
" --help | grep 'USAGE:' >/dev/null || \
    die "Test 11 failed"

# Test that the usage() function works
$PYTHON -c "from ${APP_PACKAGE} import app
def main(argv):
  app.usage()
app.run()
" 2>&1 | egrep '^  --' >/dev/null || \
    die "Test 12 failed"

# Test that shorthelp doesn't give flags in this case.
$PYTHON -c "from ${APP_PACKAGE} import app
def main(argv):
  app.usage(shorthelp=1)
app.run()
" 2>&1 | grep '^  --' >/dev/null && \
    die "Test 13 failed"

# Test writeto_stdout.
$PYTHON -c "from ${APP_PACKAGE} import app
def main(argv):
  app.usage(shorthelp=1, writeto_stdout=1)
app.run()
" | grep 'USAGE' >/dev/null || \
    die "Test 14 failed"

# Test detailed_error
$PYTHON -c "from ${APP_PACKAGE} import app
def main(argv):
  app.usage(shorthelp=1, writeto_stdout=1, detailed_error='BAZBAZ')
app.run()
" 2>&1 | grep 'BAZBAZ' >/dev/null || \
    die "Test 15 failed"

# Test exitcode
$PYTHON -c "from ${APP_PACKAGE} import app
def main(argv):
  app.usage(writeto_stdout=1, exitcode=1)
app.run()
" >/dev/null
if [ "$?" -ne "1" ]; then
  die "Test 16 failed"
fi

# Test --help (this could use wrapping which is tested elsewhere)
$PYTHON -c "from ${APP_PACKAGE} import app
def main(argv):
  print 'FAIL'
app.run()
" 2>&1 --help | grep 'USAGE: -c \[flags\]' >/dev/null || \
  die "Test 17 failed"

# Test --help does not wrap for __main__.__doc__
$PYTHON -c "from ${APP_PACKAGE} import app
import sys
def main(argv):
  print 'FAIL'
doc = []
for i in xrange(10):
  doc.append(str(i))
  doc.append('12345678 ')
  sys.modules['__main__'].__doc__ = ''.join(doc)
app.run()
" 2>&1 --help | grep '712345678 812345678' >/dev/null || \
  die "Test 18 failed"

# Test --help with forced wrap for __main__.__doc__
$PYTHON -c "from ${APP_PACKAGE} import app
import sys
def main(argv):
  print 'FAIL'
doc = []
for i in xrange(10):
  doc.append(str(i))
  doc.append('12345678 ')
  sys.modules['__main__'].__doc__ = ''.join(doc)
app.SetEnableHelpWrapping()
app.run()
" 2>&1 --help | grep '712345678 812345678' >/dev/null && \
  die "Test 19 failed"


# Test UsageError
$PYTHON -c "from ${APP_PACKAGE} import app
def main(argv):
  raise app.UsageError('You made a usage error')
app.run()
" 2>&1 | grep "You made a usage error" >/dev/null || \
  die "Test 20 failed"

# Test UsageError exit code
$PYTHON -c "from ${APP_PACKAGE} import app
def main(argv):
  raise app.UsageError('You made a usage error', exitcode=64)
app.run()
" > /dev/null 2>&1
if [ "$?" -ne "64" ]; then
  die "Test 21 failed"
fi

# Test catching top-level exceptions.  We should get the exception name on
# stderr.
./app_test_helper.py \
  --raise_exception 2>&1 | grep -q 'MyException' || die "Test 23 failed"

# Test exception handlers are called
have_handler_output=$TEST_TMPDIR/handler.txt
$PYTHON -c "from ${APP_PACKAGE} import app
def main(argv):
  raise ValueError('look for me')

class TestExceptionHandler(app.ExceptionHandler):
  def __init__(self, msg):
    self.msg = msg

  def Handle(self, exc):
    print '%s %s' % (self.msg, exc)

app.InstallExceptionHandler(TestExceptionHandler('first'))
app.InstallExceptionHandler(TestExceptionHandler('second'))
app.run()
" > $have_handler_output 2>&1
grep -q "first look for me" $have_handler_output || die "Test 24 failed"
grep -q "second look for me" $have_handler_output || die "Test 25 failed"

no_handler_output=$TEST_TMPDIR/no_handler.txt
# Test exception handlers are not called for "normal" exits
for exc in "SystemExit(1)" "app.UsageError('foo')"; do
  $PYTHON -c "from ${APP_PACKAGE} import app
def main(argv):
  raise $exc

class TestExceptionHandler(app.ExceptionHandler):
  def Handle(self, exc):
    print 'handler was called'

app.InstallExceptionHandler(TestExceptionHandler())
app.run()
" > $no_handler_output 2>&1
  grep -q "handler was called" $no_handler_output && die "Test 26 ($exc) failed"
done


# Test --help expands docstring.
$PYTHON -c "
'''USAGE: %s [flags]'''
from ${APP_PACKAGE} import app
def main(argv): print 'FAIL'
app.run()
" --help 2>&1 |
    fgrep 'USAGE: -c [flags]' >/dev/null ||
    die "Test 27 failed"


# Test --help expands docstring.
$PYTHON -c "
'''USAGE: %s --fmt=\"%%s\" --fraction=50%%'''
from ${APP_PACKAGE} import app
def main(argv): print 'FAIL'
app.run()
" --help 2>&1 |
    fgrep 'USAGE: -c --fmt="%s" --fraction=50%' >/dev/null ||
    die "Test 28 failed"


# Test --help expands docstring.
$PYTHON -c "
'''>%s|%%s|%%%s|%%%%s|%%%%%s<'''
from ${APP_PACKAGE} import app
def main(argv): print 'FAIL'
app.run()
" --help 2>&1 |
    fgrep '>-c|%s|%-c|%%s|%%-c<' >/dev/null ||
    die "Test 29 failed"


# Test bad docstring.
$PYTHON -c "
'''>%@<'''
from ${APP_PACKAGE} import app
def main(argv): print 'FAIL'
app.run()
" --help 2>&1 |
    fgrep '>%@<' >/dev/null ||
    die "Test 30 failed"

readonly HELP_PROG="
from ${APP_PACKAGE} import app
def main(argv): print 'HI'
app.run()
"


echo "PASS"
