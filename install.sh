#!/bin/sh

sudo add-apt-repository ppa:kivy-team/kivy
sudo apt-get update
sudo apt-get install python-kivy
pip install --upgrade google-api-python-client
pip install dateparser
pip install -U googlemaps
