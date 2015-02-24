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

int rotaryMotor[] = {MOTOR_L, MOTOR_R};  // Rotary encoder motor numbers
int rotaryCounter[ROTARY_COUNT] = {0};  // Counters for rotary encoders
int motorDir[ROTARY_COUNT] = {0};  // Track direction of rotary encoder motors

// Communications
SerialCommand comm;

// Grabber/kicker states, timers
boolean grabberOpen = false;
unsigned long grabTimer = 0;
boolean kickerReady = true;
unsigned long kickTimer = 0;

void setup() {
  SDPsetup();
  comm.addCommand("DRIVE", drive);
  comm.addCommand("O_GRAB", openGrabber);
  comm.addCommand("C_GRAB", closeGrabber);
  comm.addCommand("KICK", kick);
  comm.setDefaultHandler(invalidCommand);
}

void loop() {
  // Check kicker and grabber timers
  unsigned long time = millis();
  if (grabTimer && time >= grabTimer) {
    grabTimer = 0;
    motorStop(MOTOR_G);
  }
  if (kickTimer && time >= kickTimer) {
    kickTimer = 0;
    motorStop(MOTOR_K);
  }
  checkRotaryMotors();
  comm.readSerial();
}

void drive() {
  /*
   * Run drive motors L and R for given number of 'ticks' at
   * the given motor speeds.
   * Note that I haven't looped this code because we're probably
   * going to add rotary encoders to the kicker and grabber.
   * ARGS: [ack] [L_ticks] [R_ticks][L_power] [R_power]
   */
  ack(comm.next());
  
  rotaryCounter[0] = atoi(comm.next());
  rotaryCounter[1] = atoi(comm.next());
  int lPower = atoi(comm.next());
  int rPower = atoi(comm.next());
  
  // Motor L
  if (rotaryCounter[0] < 0) {
    motorDir[0] = -1;  // Bwd
    motorBackward(MOTOR_L, lPower);
  } 
  else if (rotaryCounter[0] > 0) {
    motorDir[0] = 1;  // Fwd
    motorForward(MOTOR_L, lPower);
  } 
  else { 
    motorDir[0] = 0;  // stopped
    motorStop(MOTOR_L);
  }
  
  // Motor R 
  if (rotaryCounter[1] < 0) {
    motorDir[1] = -1;
    motorBackward(MOTOR_R, rPower);
  } 
  else if (rotaryCounter[1] > 0) {
    motorDir[1] = 1;
    motorForward(MOTOR_R, rPower);
  } 
  else {
    motorDir[1] = 0;
    motorStop(MOTOR_R);
  }
}

void closeGrabber() {
  /*
   * Close the grabber with the hardcoded time and motor power
   * ARGS: [ack] [time] [power]
   */
  ack(comm.next());
  int time = atoi(comm.next());
  int power = atoi(comm.next());
  if (grabberOpen && !grabTimer) {
    motorBackward(MOTOR_G, power);
    grabberOpen = false;
    grabTimer = millis() + time;
  }
}

void openGrabber() {
  /*
   * Open the grabber with the hardcoded time and motor power
   * ARGS: [ack] [time] [power]
   */
  ack(comm.next());
  int time = atoi(comm.next());
  int power = atoi(comm.next());
  if (!grabberOpen && !grabTimer) {
    motorForward(MOTOR_G, power);
    grabberOpen = true;
    grabTimer = millis() + time;
  }
}

void kick() {
  /*
   * Run the kicker with the hardcoded time and motor power.
   * Grabber must be open.
   * ARGS: [ack] [time] [power]
   */
  ack(comm.next());
  int time = atoi(comm.next());
  int power = atoi(comm.next());
  if (grabberOpen && !kickTimer) {
    motorForward(MOTOR_K, power);
    kickTimer = millis() + time;
  }
}

void checkRotaryMotors() {
  /* Update the rotary counters and stop motors when necessary. */
  // Get rotary diffs from slave
  Wire.requestFrom(ROTARY_SLAVE_ADDRESS, ROTARY_COUNT);
  
  // Update counters and check for completion
  for (int i = 0; i < ROTARY_COUNT; i++) {
    int8_t diff = Wire.read();
    if (motorDir[i] * (rotaryCounter[i]  -= diff) <= 0) {
      motorStop(rotaryMotor[i]);
      motorDir[i] = 0;
    }
  }
}

void ack(String ack_bit) {
  Serial.println(ack_bit);
  Serial.flush();
}

void invalidCommand(const char* command) {
  Serial.print("Invalid command: ");
  Serial.println(command);
}
