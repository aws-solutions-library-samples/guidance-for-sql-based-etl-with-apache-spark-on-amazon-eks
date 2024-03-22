#!/bin/bash
#
# This script runs all tests for the root CDK project, as well as any microservices, Lambda functions, or dependency
# source code packages. These include unit tests, integration tests, and snapshot tests.
#
# It is important that this script  be tested and validated to ensure that all available test fixtures are run.
#

[ "$DEBUG" == 'true' ] && set -x
set -e

setup_python_env() {
	if [ -d "./.venv-test" ]; then
		echo "Reusing already setup python venv in ./.venv-test. Delete ./.venv-test if you want a fresh one created."
		return
	fi
	echo "Setting up python venv-test"
	python3 -m venv .venv-test
	echo "Initiating virtual environment"
	source .venv-test/bin/activate
	echo "Installing python packages"
	pip3 install -e source
	echo "deactivate virtual environment"
	deactivate
}

setup_and_activate_python_env() {
	# module_path=$1
	# cd $module_path

	[ "${CLEAN:-true}" = "true" ] && rm -fr .venv-test

	setup_python_env

	echo "Initiating virtual environment"
	source .venv-test/bin/activate
}


run_python_test() {
	module_path=$(pwd)
	module_name=${1}
	echo $1
	echo "------------------------------------------------------------------------------"
	echo "[Test] Python path=$module_path module=$module_name"
	echo "------------------------------------------------------------------------------"
	

	# setup coverage report path
	mkdir -p $source_dir/test/coverage-reports
	coverage_report_path=$source_dir/test/coverage-reports/$module_name.coverage.xml

	echo "coverage report path set to $coverage_report_path"

	# Use -vv for debugging
	python3 -m pytest --cov --cov-report=term-missing --cov-report "xml:$coverage_report_path"
	
	if [ "$?" = "1" ]; then
		echo "(source/run-all-tests.sh) ERROR: there is likely output above." 1>&2
		exit 1
	fi
	sed -i -e "s,<source>$source_dir,<source>source,g" $coverage_report_path
}

run_cdk_project_test() {
	component_description=$1
	echo "------------------------------------------------------------------------------"
	echo "[Test] $component_description"
	echo "------------------------------------------------------------------------------"
	[ "${CLEAN:-true}" = "true" ] && npm run clean
	npm install
	npm run build
	npm run test -- -u
	if [ "$?" = "1" ]; then
		echo "(source/run-all-tests.sh) ERROR: there is likely output above." 1>&2
		exit 1
	fi
	[ "${CLEAN:-true}" = "true" ] && rm -fr coverage
}

run_source_unit_test() {
	echo "------------------------------------------------------------------------------"
	echo "[Test] Run source unit tests"
	echo "------------------------------------------------------------------------------"

	# Test the functions
	cd $source_dir
	for folder in */; do
		if [ "$folder" = "test/" ]; then
			echo "------------------------------------------------------------------------------"
			echo "[Test] Run tests against $folder"
			echo "------------------------------------------------------------------------------"
			pip3 install -r $folder/requirement-test.txt
			run_python_test $folder
			rm -rf *.egg-info
		fi
		cd $source_dir
	done
}

# Clean the test environment before running tests and after finished running tests
# The variable is option with default of 'true'. It can be overwritten by caller
# setting the CLEAN environment variable. For example
#    $ CLEAN=true ./run-all-tests.sh
# or
#    $ CLEAN=false ./run-all-tests.sh
#
CLEAN="${CLEAN:-true}"

setup_and_activate_python_env
source_dir=$PWD/source
cd $source_dir

python --version
run_source_unit_test

# Return to the root/ level where we started
cd $source_dir