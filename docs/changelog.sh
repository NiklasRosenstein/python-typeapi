#!/bin/bash
set -x
cd $(dirname $(dirname $PWD/"$0"))
slap changelog format --all --markdown > docs/docs/meta/changelog.md
