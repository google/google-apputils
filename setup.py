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

# NB: this requires setuptools be installed.
# Try sudo apt-get install python-setuptools
from setuptools import setup, find_packages

from google.apputils import setup_command

REQUIRE = [
    "python-dateutil>=1.4",
    "python-gflags>=1.3",
    "pytz>=2010",
    ]

setup(
    name = "google-apputils",
    version = "0.2",
    packages = find_packages(exclude=["tests"]),
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
    # up the command and option mappings, for this project only.
    cmdclass = {"google_test": setup_command.GoogleTest},
    command_options = {"google_test": {"test_dir": ("setup.py", "tests")}},

    author = "Google Inc.",
    author_email="opensource@google.com",
    url="http://code.google.com/p/google-apputils-python",
    )
