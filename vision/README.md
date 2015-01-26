# Vision from Group 7 (Last Year)

This readme serves to help explain installation until appropiate scripts are written for this section which will ease installation.

This section assumes one is working on a DiCE machine but is hypothetically posibble to work with on own laptop (the path names will be slightly different)

## Installing the required packages

Installation of the required packages for group 7s vision system using opencv can be performed via the following set of commands.

### Via pip in a virtualenv (Works in DiCE)

This assumes that a virtualenv running python 2.7.x has been created.

```Shell
pip install Polygon2 argparse pyserial
``` 

### Via pip to a local install (Works in DiCE)

By using the `user` flag with pip, the following packages/libraries will be installed on the `.local` folder inside the Home Directory

```Shell
pip install Polygon2 argparse pyserial --user
```

More will follow or otherwise figure it out for yourself by going through what is remaining on the repository readme from last years group 7.




