# Arduino-related code and config  

The main sketch is for planner or parameterized control.
The manualcontrol sketch is for use with the python manualcontrol class.

## Sensor Information ##
The rotary sensor is a quadrature rotary encoder, It has 24 pulses per revolution yielding a 15 degree ungeared accuracy.
The sensor board has accepts up to 6 sensors, the library proviced can either poll if sensors > 2 and use interrupts when less than 2.
The board interfaces on the i2C bus, and the arduino should be set to poll the sensor at every clock cycle. 

## Misc. notes
* Consider port manipulation for speedup and code shrink. See: arduino.cc/en/Reference/PortManipulation  
* Currently using the SerialCommand library at https://github.com/kroimon/Arduino-SerialCommand  

