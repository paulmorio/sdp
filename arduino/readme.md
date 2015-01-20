# Arduino-related code and config

## How I learned to stop worrying and love RF  
* RF most likely won't work if the xino is powered via some USB wall charger from i.e. your phone. For likely similar reasons it will not work if the board is powered by USB via a machine on standby.  
* Power the SRF first. The xino will attempt to connect on boot only - of course you can reset it to encourage it to connect but the reset button on our board is unreliable at best.  

## Config  
The guard character is '~' rather than the default '+'. Do not change this.  
There is a 5 second inactivity timeout once in config mode.  

### SRF stick  
1. Connect the SRF stick to the computer and open a serial connection with `screen /dev/tty.usbmodem000001 115200` for example.  
2. Type '~~~' (no newline/enter) to enter command mode - the device should respond with 'OK'.  

From now on, hit enter after each command.  

* ATRE    -   Reset to factory defaults - NB THIS CHANGES THE GUARD CHAR TO +  
* ATMY G7    -   Set node ID for secure remote programming  
* ATRP1  -   Allow wireless reprogramming of the Arduino  
* ATID0007   -   Set the pan ID to 0x0007.  
* ATEA LuckyNumberSeven  -   Set encryption key  
* ATEE 1     -   Enable encrytion  
* ATWR       -   Write changes to flash (skip this if testing and you want changes to revert on power down)  
* ATAC       -   Apply changes  
* ATDN       -   Exit command mode   

### Xino RF Chip  
1. Connect the Xino RF via USB and open a serial connection  
2. Type '~~~' (no newline/enter) to enter command mode - the device should respond with 'OK'  

From now on, hit enter after each command  

* ATRE   -   Reset to factory defaults  
* ATBD1C200  -   Set baudrate to 115200  
* ATID0007   -   Set the pan ID - match SRF  
* ATMY G7     -   Set node ID  
* ATEA LuckyNumberSeven  -   Set encryption key  
* ATEE 1     -   Enable encryption  
* ATWR       -   Write changes to flash  
* ATAC   -   Apply changes  
* ATDN   -   Exit command mode  

## Misc. notes
* Consider port manipulation for speedup and code shrink. See: arduino.cc/en/Reference/PortManipulation  
* Currently using the SerialCommand library at https://github.com/kroimon/Arduino-SerialCommand  
