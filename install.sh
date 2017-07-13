sudo apt update
sudo apt install -y python-pip virtualenv tmux
#git clone https://gascarcella@bitbucket.org/pstsrl/twistreapy.git
#cd twistreapy/
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
cd src/
cp config.ini.prod config.ini
exit
