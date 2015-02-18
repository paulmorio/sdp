/*
  Arduino slave sketch for SDP Group 7 2014
  
  This sketch is used with the main arduino sketch on master.
  
  This code reads the two rotary sensors and returns a delta on request.
  Origin is 0, resolution is 15 degrees[??]
*/

#include <Rotary.h>
#include <Wire.h>

Rotary motorL = Rotary(0, 1);
Rotary motorR = Rotary(4, 5);
signed char motorLDiff = 0;
signed char motorRDiff = 0;

void setup() {
  Wire.begin(5);
  Wire.onRequest(requestEvent);
}

void loop() {
  unsigned char motorLResult = motorL.process();
  unsigned char motorRResult = motorR.process();
  if (motorLResult) motorLResult == DIR_CW ? motorLDiff-- : motorLDiff++ ;
  if (motorRResult) motorRResult == DIR_CW ? motorRDiff-- : motorRDiff++ ;
}

void requestEvent() {
  // Write the difference since last call then reset status counters
  // NB: we send positive difference as we already know which direction the motor is spinning
  // NB: this must be called frequently by the master else overflow is likely
  if (motorLDiff < 0) motorLDiff = -motorLDiff;
  if (motorRDiff < 0) motorRDiff = -motorRDiff;
  Wire.write((motorLDiff << 8) + motorRDiff);  // Left then right
  motorLDiff = 0;
  motorRDiff = 0;
}


