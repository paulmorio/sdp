#include <Rotary.h>
#include <Wire.h>

Rotary leftMotor = Rotary(2, 3);
Rotary rightMotor = Rotary(4, 5);
int8_t lMotorDiff = 0;
int8_t rMotorDiff = 0;

void setup() {
  Wire.begin(5);
  Wire.onRequest(sendDiffs);
}

void loop() {
  unsigned char lMotorResult = leftMotor.process();
  if (lMotorResult) {
    if (lMotorResult == DIR_CW) lMotorDiff++;
    else if (lMotorResult == DIR_CCW) lMotorDiff--;
  }
  
  unsigned char rMotorResult = rightMotor.process();
  if (rMotorResult) {
    if (rMotorResult == DIR_CW) rMotorDiff++;
    else if (rMotorResult == DIR_CCW) rMotorDiff--;
  }
}

void sendDiffs() {
  Wire.write(lMotorDiff);
  Wire.write(rMotorDiff);
  lMotorDiff = 0;
  rMotorDiff = 0;
}

