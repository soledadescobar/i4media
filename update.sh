#!/usr/bin/env bash
git stash --keep-index
git pull

chmod +x install.stream.sh
. ./install-stream.sh