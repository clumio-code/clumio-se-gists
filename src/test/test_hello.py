#!/usr/bin/env python3
#
# Copyright 2024. Clumio, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Google Style 4 spaces, 100 columns:
#   https://google.github.io/styleguide/pyguide.html
#

"""Sample unittest script for the clumio-se-gists repository."""

from __future__ import annotations

import unittest

from .. import hello


class TestHello(unittest.TestCase):
    def test_parse_args(self) -> None:
        self.assertEqual(hello.parse_args(['--name', 'Alice']).name, 'Alice')


if __name__ == '__main__':
    unittest.main()
