 # This script will create a Python 2.7 virtual environment
 # with dependencies (see requirements.txt) in the project 
 # root directory.
 # Note that this is for use on UoE DICE machines only - I 
 # am making several assumptions based on this.
 # If you are met with 'Permission denied' then you should
 # set permissions with chmod - i.e `chmod 777 this_script.sh`

 virtualenv --distribute --python=/usr/bin/python2.7 ../venv
 source ../venv/bin/activate
 pip install -r requirements.txt
 deactivate

 # This should "install" OpenCV, give that it can't be pip'd
 # The "clean" way to do this:
 # http://stackoverflow.com/questions/11184847/running-opencv-from-a-python-virtualenv/24112175#24112175
 # This appears to require building OpenCV, though, which takes a very long time.
 # cp ../OpenCV/* ../venv/lib/python2.7/site-packages/
