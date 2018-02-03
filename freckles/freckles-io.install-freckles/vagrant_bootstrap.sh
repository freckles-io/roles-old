#!/usr/bin/env bash

export DEBIAN_FRONTEND=noninteractive

set -x
set -e

# if [ -d "/pip" ]; then
#    rm -f .pip
#    ln -s /pip "$HOME/.pip"
# fi

# create freckles virtualenv
BASE_DIR="$HOME/.local/"
FRECKLES_DIR="$BASE_DIR/install-freckles"
FRECKLES_VIRTUALENV_BASE="$FRECKLES_DIR/venv/"
FRECKLES_VIRTUALENV="$FRECKLES_VIRTUALENV_BASE/ansible"
FRECKLES_VIRTUALENV_ACTIVATE="$FRECKLES_VIRTUALENV/bin/activate"
export WORKON_HOME="$FRECKLES_VIRTUALENV"

sudo apt-get update || sudo apt-get update
sudo apt-get install -y build-essential git python-dev python-virtualenv libssl-dev libffi-dev libsqlite3-dev

mkdir -p "$FRECKLES_VIRTUALENV"
cd "$FRECKLES_VIRTUALENV_BASE"
virtualenv --system-site-packages ansible

# install freckles & requirements
source ansible/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools wheel
pip install ansible
pip install ansible-toolbox

echo source "$FRECKLES_VIRTUALENV_ACTIVATE" >> "$HOME/.bashrc"

