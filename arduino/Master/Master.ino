/*
  Arduino code for SDP Group 7 2014
  
  This sketch is for use with planner control.
  
  This code implements an alternating bit protocol for use with the
  robot.py module. Please adhere to the existing examples when writing
  code as failing to acknowledge commands will result in very bad things.
*/

#include <SDPArduino.h>
#include <SerialCommand.h>
#include <Wire.h>

// Motor numbers
#define MOTOR_L 0
#define MOTOR_R 2
#define MOTOR_K 4
#define MOTOR_G 5

// Rotary encoder
#define ROTARY_SLAVE_ADDRESS 5
#define ROTARY_COUNT 2
#define SENSOR_COUNT 1

int rotaryMotor[] = {MOTOR_L, MOTOR_R};  // Rotary encoder motor numbers
int rotaryCounter[ROTARY_COUNT] = {0};  // Counters for rotary encoders
int motorDir[ROTARY_COUNT] = {0};  // Track direction of rotary encoder motors

// Communications
SerialCommand comm;

// Grabber/kicker states, timers
boolean grabberOpen = true;  // Assume open on startup
boolean isMoving = false;
boolean isKicking = false;
boolean isGrabbing = false;
boolean ballGrabbed = false;
unsigned long grabTimer = 0;
unsigned long kickTimer = 0;

void setup() {
  SDPsetup();
  comm.addCommand("DRIVE", drive);
  comm.addCommand("O_GRAB", openGrabber);
  comm.addCommand("C_GRAB", closeGrabber);
  comm.addCommand("KICK", kick);
  comm.addCommand("STATUS", ack);
  comm.setDefaultHandler(invalidCommand);
}

void loop() {
  checkTimers();
  checkSensors();
  comm.readSerial();
}

void drive() {
  /*
   * Run drive motors L and R for given number of 'ticks' at
   * the given motor speeds.
   * Note that I haven't looped this code because we're probably
   * going to add rotary encoders to the kicker and grabber.
   * ARGS: [L_ticks] [R_ticks][L_power] [R_power] [ack]
   */  
  rotaryCounter[0] = atoi(comm.next());
  rotaryCounter[1] = atoi(comm.next());  // Sensor is mounted backward
  int lPower = atoi(comm.next());
  int rPower = atoi(comm.next());
  
  // Motor L
  if (rotaryCounter[0] < 0) {
    isMoving = true;
    motorDir[0] = -1;  // Bwd
    motorBackward(MOTOR_L, lPower);
  } 
  else if (rotaryCounter[0] > 0) {
    isMoving = true;
    motorDir[0] = 1;  // Fwd
    motorForward(MOTOR_L, lPower);
  } 
  else { 
    motorDir[0] = 0;  // stop on next test
  }
  
  // Motor R 
  if (rotaryCounter[1] < 0) {
    isMoving = true;
    motorDir[1] = -1;
    motorBackward(MOTOR_R, rPower);
  } 
  else if (rotaryCounter[1] > 0) {
    isMoving = true;
    motorDir[1] = 1;
    motorForward(MOTOR_R, rPower);
  } 
  else {
    motorDir[1] = 0;
  }
  ack();
}

void closeGrabber() {
  /*
   * Close the grabber with the hardcoded time and motor power
   * ARGS: [time] [power] [ack]
   */
  int time = atoi(comm.next());
  int power = atoi(comm.next());
  motorBackward(MOTOR_G, power);
  grabTimer = millis() + time;
  isGrabbing = true;
  ack();
}

void openGrabber() {
  /*
   * Open the grabber with the hardcoded time and motor power
   * ARGS: [time] [power] [ack]
   */
  int time = atoi(comm.next());
  int power = atoi(comm.next());
  motorForward(MOTOR_G, power);
  grabTimer = millis() + time;
  isGrabbing = true;
  ack();
}

void kick() {
  /*
   * Run the kicker with the hardcoded time and motor power.
   * Grabber must be open.
   * ARGS: [ack] [time] [power]
   */
  int time = atoi(comm.next());
  int power = atoi(comm.next());
  motorForward(MOTOR_K, power);
  kickTimer = millis() + time;
  ack();
}

void checkTimers() {
  /* Check kicker and grabber timers */
  unsigned long time = millis();
  if (grabTimer && time >= grabTimer) {  // Grab timer test
    motorStop(MOTOR_G);
    grabTimer = 0;
    grabberOpen = !grabberOpen;
    isGrabbing = false;
  }
  if (kickTimer && time >= kickTimer) {  // Kick timer test
    kickTimer = 0;
    isKicking = false;
    motorStop(MOTOR_K);
  }
}

void checkSensors() {
  /* Update the sensor states/counters and stop motors if necessary */
  // Get rotary diffs from slave
  Wire.requestFrom(ROTARY_SLAVE_ADDRESS, ROTARY_COUNT + SENSOR_COUNT);
  
  // Update counters and check for completion
  for (int i = 0; i < ROTARY_COUNT; i++) {
    int8_t diff = Wire.read();
    if (motorDir[i] * (rotaryCounter[i]  -= diff) <= 0) {
      motorStop(rotaryMotor[i]);
      motorDir[i] = 0;
    }
  }
  // Update grabbed state
  uint8_t grabberSwitchState = Wire.read();  // non-zero if not grabbed
  if (grabberSwitchState) ballGrabbed = false;
  else ballGrabbed = true;
  
  // Update moving state
  if (motorDir[0] == 0 && motorDir[1] == 0) isMoving = false;
}

void ack() {
  char ack_bit = comm.next()[0];
  Serial.print(ack_bit);
  if (grabberOpen) Serial.print(1);
  else Serial.print(0);
  if (isGrabbing) Serial.print(1);
  else Serial.print(0);
  if (isMoving) Serial.print(1);
  else Serial.print(0);
  if (isKicking) Serial.print(1);
  else Serial.print(0);
  if (ballGrabbed) Serial.println(1);
  else Serial.println(0);
  Serial.flush();
}

void invalidCommand(const char* command) {
}
