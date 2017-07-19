apt update
apt install -y python-pip python-systemd
pip install -r requirements.txt
cp -f i4media-twitter.sh /etc/init.d/i4media-twitter.sh
chmod +755 /etc/init.d/i4media-twitter.sh
systemctl daemon-reload
service i4media-twitter start
exit
