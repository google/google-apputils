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
# Owner: unittest-team@google.com

EXE=./basetest_test.py
function die {
	echo "$1"
	exit $2
}

# Create directories for use
function MaybeMkdir {
    for dir in $@; do
	if [ ! -d "$dir" ] ; then
	    mkdir "$dir" || die "Unable to create $dir"
	fi
    done
}

# TODO(dborowitz): Clean these up if we die.
MaybeMkdir abc cba def fed ghi jkl

# Test assertListEqual, assertDictEqual, and assertSameElements
$EXE --testid=5 || die "Test 5 failed" $?

# Test assertAlmostEqual and assertNotAlmostEqual
$EXE --testid=6 || die "Test 6 failed" $?

# Test that tests marked as "expected failure" but which passes
# cause an overall failure.
$EXE --testid=7 && die "Test 7 passed unexpectedly" $?
output=$($EXE --testid=8 -- -v 2>&1) && die "Test 8 passed unexpectedly" $?
printf '%s\n' "$output"
grep '^FAILED (expected failures=1, unexpected successes=1)' <<<"$output" \
  && grep '^testDifferentExpectedFailure .* unexpected success' <<<"$output" \
  && grep '^testExpectedFailure .* expected failure' <<<"$output" \
  || die "Test 8 didn't write expected diagnostic"

# Invoke with no env vars and no flags
(
unset TEST_RANDOM_SEED
unset TEST_SRCDIR
unset TEST_TMPDIR
$EXE --testid=1
) || die "Test 1 failed" $?

# Invoke with env vars but no flags
(
export TEST_RANDOM_SEED=321
export TEST_SRCDIR=cba
export TEST_TMPDIR=fed
$EXE --testid=2
) || die "Test 2 failed" $?

# Invoke with no env vars and all flags
(
unset TEST_RANDOM_SEED
unset TEST_SRCDIR
unset TEST_TMPDIR
$EXE --testid=3 --test_random_seed=123 --test_srcdir=abc --test_tmpdir=def
) || die "Test 3 failed" $?

# Invoke with env vars and all flags
(
export TEST_RANDOM_SEED=321
export TEST_SRCDIR=cba
export TEST_TMPDIR=fed
$EXE --testid=4 --test_random_seed=123 --test_srcdir=abc --test_tmpdir=def
) || die "Test 4 failed" $?

# Cleanup
rm -r abc cba def fed ghi jkl
echo "Pass"
