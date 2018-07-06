#!/usr/bin/env bash
sudo cp -f twitter-stream.sh /etc/init.d/i4media.twitter-stream.sh
sudo chmod +755 /etc/init.d/i4media.twitter-stream.sh
sudo systemctl daemon-reload