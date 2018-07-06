#!/usr/bin/env bash
GREEN=`tput setaf 2`
RED=`tput setaf 1`
BLUE=`tput setaf 3`
RESET=`tput sgr0`

echo "${BLUE}Installing Streaming Service${RESET}"
sudo cp -f twitter-stream.sh /etc/init.d/i4media.twitter-stream.sh
sudo chmod +755 /etc/init.d/i4media.twitter-stream.sh
sudo systemctl daemon-reload