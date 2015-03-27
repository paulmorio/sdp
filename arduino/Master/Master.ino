/*
  Arduino code for SDP Group 7 2014
  
  This sketch is for use with planner control.
  
  This code implements an alternating bit protocol for use with the
  robot.py module. Please adhere to the existing examples when writing
  code as failing to acknowledge commands will result in very bad things.
*/

#include <SDPArduinoBrake.h>
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
#define ROTARY_TIMEOUT 1000  // cycles

int rotaryMotor[] = {MOTOR_L, MOTOR_R};  // Rotary encoder motor numbers
int rotaryCounter[ROTARY_COUNT] = {0};  // Counters for rotary encoders
int motorDir[ROTARY_COUNT] = {0};  // Track direction of rotary encoder motors
int rotaryTimeout[ROTARY_COUNT] = {-1};  // Counters for rotary timeout

// Communications
SerialCommand comm;
bool currentAckBit = false;

// Grabber/kicker states, timers
boolean grabberOpen = true;  // Assume open on startup
boolean isMoving = false;
boolean isKicking = false;
boolean isGrabbing = false;
boolean ballGrabbed = false;
unsigned long grabTimer = 0;
unsigned long kickTimer = 0;

// TODO check the ack bit on incoming commands
// TODO braking
// TODO tidy 
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
   * Run drive motors L and R for given number of 'ticks' at the given motor speeds.
   * ARGS: [ack] [L_ticks] [R_ticks][L_power] [R_power]
   */  
  if (!ackTest()) return;
  rotaryCounter[0] = atoi(comm.next());
  rotaryCounter[1] = atoi(comm.next());
  int lPower = atoi(comm.next());
  int rPower = atoi(comm.next());
  
  // Start motors if necessary
  // Motor L
  if (motorDir[0] != -1 && rotaryCounter[0] < 0) {
    isMoving = true;
    motorDir[0] = -1;  // Bwd
    motorBackward(MOTOR_L, lPower);
  } 
  else if (motorDir[0] != 1 && rotaryCounter[0] > 0) {
    isMoving = true;
    motorDir[0] = 1;  // Fwd
    motorForward(MOTOR_L, lPower);
  } 
  
  // Motor R 
  if (motorDir[1] != -1 && rotaryCounter[1] < 0) {
    isMoving = true;
    motorDir[1] = -1;
    motorBackward(MOTOR_R, rPower);
  } 
  else if (motorDir[1] != 1 && rotaryCounter[1] > 0) {
    isMoving = true;
    motorDir[1] = 1;
    motorForward(MOTOR_R, rPower);
  } 
  ack();
}

void closeGrabber() {
  /*
   * Close the grabber with the hardcoded time and motor power
   * ARGS: [ack] [time] [power]
   * TODO: rotary grabber
   */
  if (!ackTest()) return;
  int time = atoi(comm.next());
  int power = atoi(comm.next());
  if (!isGrabbing) {
    motorBackward(MOTOR_G, power);
    grabTimer = millis() + time;
    isGrabbing = true;
  }
  ack();
}

void openGrabber() {
  /*
   * Open the grabber with the hardcoded time and motor power
   * ARGS: [time] [power] [ack]
   * TODO rotary grabber
   */
  if (!ackTest()) return;
  int time = atoi(comm.next());
  int power = atoi(comm.next());
  if (!isGrabbing) {
    motorForward(MOTOR_G, power);
    grabTimer = millis() + time;
    isGrabbing = true;
  }
  ack();
}

void kick() {
  /*
   * Run the kicker with the hardcoded time and motor power.
   * Grabber must be open.
   * ARGS: [ack] [time] [power]
   * TODO: rotary kicker
   */
  if (!ackTest()) return;
  int time = atoi(comm.next());
  int power = atoi(comm.next());
  if (!isKicking) {
    motorForward(MOTOR_K, power);
    kickTimer = millis() + time;
    isKicking = true;
  }
  ack();
}

void checkTimers() {
  /* Check kicker and grabber timers */
  unsigned long time = millis();
  if (isGrabbing && time >= grabTimer) {  // Grab timer test
    motorStop(MOTOR_G);
    grabTimer = 0;
    grabberOpen = !grabberOpen;
    isGrabbing = false;
  }
  if (isKicking && time >= kickTimer) {  // Kick timer test
    kickTimer = 0;
    isKicking = false;
    motorStop(MOTOR_K);
  }
}

void checkSensors() {
  /* Update the sensor states/counters and stop motors if necessary */

  // Poll sensor board
  Wire.requestFrom(ROTARY_SLAVE_ADDRESS, ROTARY_COUNT + SENSOR_COUNT);
  
  // Update counters and check for completion
  for (int i = 0; i < ROTARY_COUNT; i++) {
    int8_t diff = Wire.read();  // Read i-th value

    /* 
      We set a timeout upon receiving a diff of 0 on an active motor.
      This is to allow the motor to stop moving when it is, e.g., running
      against a wall.
    */
    if (diff == 0 && motorDir[i] != 0) {
      if (rotaryTimeout[i] == -1) rotaryTimeout[i] = ROTARY_TIMEOUT;
      else if (--rotaryTimeout[i] == 0) rotaryCounter[i] = 0;
    }
    else {  // Reset timeout upon receiving non-zero
      rotaryTimeout[i] = -1;
    }

    /* Subtract diff and check */
    // TODO stop motors in one call
    if (motorDir[i] && motorDir[i] * (rotaryCounter[i]  -= diff) <= 0) {
      motorStop(rotaryMotor[i]);
      motorDir[i] = 0;
      rotaryTimeout[i] = -1;
    }
  }

  ballGrabbed = !Wire.read();
  isMoving = !(motorDir[0] == 0 && motorDir[1] == 0);
}

bool ackTest() {
  char ackBit = comm.next()[0];
  if (ackBit != castToChar(currentAckBit)) {
    comm.clearBuffer();  // Flush remaining args
    return false;
  }
  return true;
}

void ack() {
  Serial.print(castToChar(currentAckBit));
  currentAckBit = !currentAckBit;  // Flip expected ack bit
  Serial.print(castToChar(grabberOpen));
  Serial.print(castToChar(isGrabbing));
  Serial.print(castToChar(isMoving));
  Serial.print(castToChar(isKicking));
  Serial.println(castToChar(ballGrabbed));
  Serial.flush();
}

char castToChar(boolean b) {
  if (b) return '1';
  else return '0';
}
void invalidCommand(const char* command) {
}
