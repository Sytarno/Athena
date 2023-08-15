#!/bin/sh

echo "Attempting to install libraries"

sudo apt install default-jre
sudo apt install python3-pip

pip install -U py-cord --pre
pip install Pillow
pip install numpy
pip install wavelink
pip install spotipy
pip install validators