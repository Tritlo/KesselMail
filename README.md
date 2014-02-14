Kessel Mail
===========

A bot that reads email, and converts any pdf files to their smaller tex equivalents.

To use:

first, create a virtual env

    virtualenv venv -ppython2
	
next install depenencies

    pip install -r requirements.txt
	
then, change the settings in the kesselmail.conf file for your needs

now, run with

    honcho -e kesselmail.conf run python KesselMail.py
	
A supervisord config is provided, and assumes an installation in the directory

    /var/KesselMail
