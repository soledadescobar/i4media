sudo apt update
sudo apt install -y python-pip virtualenv tmux
git clone https://gascarcella:gorila38@bitbucket.org/pstsrl/twistreapy.git
cd twistreapy/
git config user.name "i4media-develop"
git config user.email "develop@i4media.com"
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
cd src/
cp config.ini.prod config.ini
exit

