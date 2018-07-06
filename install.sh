#!/usr/bin/env bash
GREEN=`tput setaf 2`
RED=`tput setaf 1`
BLUE=`tput setaf 3`
RESET=`tput sgr0`

GIT_USERNAME="gascarcella"
GIT_PASSWORD="gorila38"

GIT_URL="https://$GIT_USERNAME:$GIT_PASSWORD@github.com/gascarcella/i4media.git"

DEFAULT_FOLDER=/usr/lib/i4media

command -v git >/dev/null 2>&1 || {
    echo "${RED}GIT Not detected.${BLUE}Installing${RESET}"
    sudo apt update
    sudo apt install -y git
}

command -v python3 >/dev/null 2>&1 || {
    echo "Python3 Not detected. Installing"
    sudo apt update
    sudo apt install -y python3
}
command -v pip3 >/dev/null 2>&1 || {
    echo "Pip3 Not detected. Installing"
    sudo apt update
    sudo apt install -y python3-pip
}
echo "${BLUE}Trying to install python3-systemd tools${RESET}"
sudo apt install python3-systemd

echo "${GREEN}====================================================${RESET}"
echo " "
echo "${BLUE}Specify installation folder. Leave blank for default [$DEFAULT_FOLDER]${RESET}"

read -p "${BLUE}Absolute Path: ${GREEN}[$DEFAULT_FOLDER]${RESET}" OUTPUT_FOLDER

:${OUTPUT_FOLDER:=${DEFAULT_FOLDER}}

echo "${BLUE}Creating Output Folder $OUTPUT_FOLDER${RESET}"
sudo mkdir -p ${OUTPUT_FOLDER}
sudo chown ${USER}:${USER} ${OUTPUT_FOLDER}

echo "${BLUE}Entering $OUTPUT_FOLDER${RESET}"
cd ${OUTPUT_FOLDER}

git clone ${GIT_URL}
cd i4media

echo "${BLUE}Installing PIP Requirements${RESET}"
sudo -H pip3 install -r requirements.txt

chmod +x install-stream.sh
./install-stream.sh

if [ "$OUTPUT_FOLDER" != "$DEFAULT_FOLDER" ]; then
    echo "${RED}You are not using the default folder. Remember to edit /etc/init.d/i4media.twitter-stream.sh with the fixed path${RESET}"
fi

echo "${GREEN}Finish${RESET}"
exit
