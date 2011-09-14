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

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages
from setuptools.command import test

REQUIRE = [
    "python-dateutil>=1.4",
    "python-gflags>=1.4",
    "pytz>=2010",
    ]


# Mild hackery to get around the fact that we want to include a
# GoogleTest as one of the cmdclasses for our package, but we
# can't reference it until our package is installed. We simply
# make a wrapper class that actually creates objects of the
# appropriate class at runtime.
class GoogleTestWrapper(test.test):
  test_dir = None

  def __new__(cls, *args, **kwds):
    from google.apputils import setup_command
    dist = setup_command.GoogleTest(*args, **kwds)
    dist.test_dir = GoogleTestWrapper.test_dir
    return dist

setup(
    name = "google-apputils",
    version = "0.2.2",
    packages = find_packages(exclude=["tests"]),
    scripts = ["ez_setup.py"],
    entry_points = {
        "distutils.commands": [
            "google_test = google.apputils.setup_command:GoogleTest",
            ],

        "distutils.setup_keywords": [
            ("google_test_dir = google.apputils.setup_command"
             ":ValidateGoogleTestDir"),
            ],
        },

    install_requires = REQUIRE,
    tests_require = REQUIRE + ["mox>=0.5"],

    # The entry_points above allow other projects to understand the
    # google_test command and test_dir option by specifying
    # setup_requires("google-apputils"). However, those entry_points only get
    # registered when this project is installed, and we need to run Google-style
    # tests for this project before it is installed. So we need to manually set
    # up the command and option mappings, for this project only, and we use
    # a wrapper class that exists before the install happens.
    cmdclass = {"google_test": GoogleTestWrapper},
    command_options = {"google_test": {"test_dir": ("setup.py", "tests")}},

    author = "Google Inc.",
    author_email="opensource@google.com",
    url="http://code.google.com/p/google-apputils-python",
    )
