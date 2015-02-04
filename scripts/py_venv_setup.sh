#!/bin/sh
 # This script will create a Python 2.7 virtual environment
 # with dependencies (see requirements.txt) in the project 
 # root directory.
 # Note that this is for use on UoE DICE machines only - I 
 # am making several assumptions based on this.
 # If you are met with 'Permission denied' then you should
 # set permissions with chmod - i.e `chmod 777 this_script.sh`

 virtualenv --distribute --python=/usr/bin/python2.6 ../venv
 source ../venv/bin/activate
 pip install -r requirements.txt
 deactivate
