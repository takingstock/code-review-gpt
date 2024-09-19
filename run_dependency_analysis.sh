#!/bin/bash

## lets use env variables to indicate temp files and folders .. these WILL be deleted at the end of this script
export CHANGES_JSON='./changes.json'
export ROOT_CHANGES_JSON='../../../changes.json'
export PY_DOWNSTREAM_USAGE='./py_downstream_usage.json'
export NODEJS_DOWNSTREAM_USAGE='./nodejs_downstream_usage.json'
export GIT_DIFF_FILE='./diff.txt'

export HOME_DIR='./'
export NODEJS_DEPENDENCY_CODE_DIR='./src/dependency_tree/nodejs_ts/'
export PY_DEPENDENCY_CODE_DIR='./src/dependency_tree/py/'
export DIFF_PROCESSOR='generate_dependency_inputs.js'

export NODEJS_DEPENDENCY_EXTRACTION='nodejs_extractor.js'
export PY_DEPENDENCY_EXTRACTION='generate_dependency.py'
## generate diff file
git diff -U0 --diff-filter=AMRT > $GIT_DIFF_FILE

## process the diff file and generate the source file for py and nodejs to generate dependency details
## the processor is in nodejs BUT it might as well be in any language
echo "Running the command => node $NODEJS_DEPENDENCY_CODE_DIR$DIFF_PROCESSOR"
node "$NODEJS_DEPENDENCY_CODE_DIR$DIFF_PROCESSOR"

## just call the node and py dependency generators
echo "Running node:: $NODEJS_DEPENDENCY_CODE_DIR$NODEJS_DEPENDENCY_EXTRACTION"
echo "Running   py:: $PY_DEPENDENCY_CODE_DIR$PY_DEPENDENCY_EXTRACTION"

cd $NODEJS_DEPENDENCY_CODE_DIR
node "$NODEJS_DEPENDENCY_EXTRACTION"

cd -

cd $PY_DEPENDENCY_CODE_DIR
python "$PY_DEPENDENCY_EXTRACTION"

cd -

## now delete the temp files including but not limited to diff file, changes json
rm -f $GIT_DIFF_FILE
rm -f $CHANGES_JSON

echo "Please check $NODEJS_DEPENDENCY_CODE_DIR/$NODEJS_DOWNSTREAM_USAGE for nodejs dependency list"
echo "Please check $PY_DEPENDENCY_CODE_DIR/$PY_DOWNSTREAM_USAGE for nodejs dependency list"
