# Communications
Using the RXTX library from github.com/rxtx/rxtx. 
TODO:  
*Run on DICE, etc. - the arduino has a different name on each platform (hooray).  
*Include RXTX library in project as a dependency -- use maven (NB: 32-bit VM only, run with -d32)  
*Switch to InputStreamReader if possible - buffering and reading strings may be notably slower than using integer codes and an inputstream
