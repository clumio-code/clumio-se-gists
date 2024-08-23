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

# Install with the CI dependencies.
install-ci:
	pip install -r requirements-ci.txt


# Install with the development dependencies.
install-dev:
	pip install -r requirements-dev.txt


lint:
	ruff check

mypy:
	mypy --config mypy.ini .

test:
	rm -rf build/test_reports
	mkdir -p build/test_reports/py
	green -r -j build/test_reports/py/clumio-se-gists-pytests.xml src
	python -m coverage xml --rcfile .coveragerc -o build/test_reports/py/clumio-se-gists-pycoverage.xml


format:
	ruff check --fix-only
	ruff format


all: install-ci lint mypy test

# Install pre-commit hooks
pre_commit:
	pre-commit install

# Install pre-push hooks
pre_push:
	pre-commit install --hook-type=pre-push

.PHONY: install-ci install-dev lint mypy test format all pre_commit pre_push
