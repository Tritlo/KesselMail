Kessel Mail
===========

A bot that reads email, and converts any pdf files to their smaller tex equivalents.

Requires inkscape to be installed.

To use:

first, create a virtual env

    virtualenv venv -ppython2
	
next install depenencies

    pip install -r requirements.txt
	
then, change the settings in the kesselmail.conf file for your needs

now, run with

    honcho -e kesselmail.conf run python KesselMail.py
	
A supervisord config is provided with kesselmail.ini, and assumes an installation in the directory

    /var/KesselMail
	
Placing it in /etc/supervisor.d/, and following the instructions at 

http://supervisord.org/running.html

should start it as a daemon.
