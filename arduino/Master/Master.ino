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

#define MOVE_PWR 100

// Kicker and grabber constants
#define KICK_POWER 100
#define KICK_TIME 500
 
#define GRAB_POWER 100
#define GRAB_TIME 220

// Command parser
SerialCommand comm;

// States and counters
boolean grabberOpen = false;
unsigned long grabTimer = 0;
boolean kickerReady = true;
unsigned long kickTimer = 0;
int motorLDist = 0;
int motorLDir = 0;  // -1 bw, 0 stopped; 1 fwd
int motorRDist = 0;
int motorRDir = 0;

void setup() {
  SDPsetup();
  comm.addCommand("MOVE", move);
  comm.addCommand("O_GRAB", openGrabber);
  comm.addCommand("C_GRAB", closeGrabber);
  comm.addCommand("KICK", kick);
  comm.addCommand("READY", isReady);
  comm.setDefaultHandler(invalidCommand);
}

void loop() {
  // Check kicker and grabber timers
  time = millis();
  if (grabTimer && time >= grabTimer) {
    grabTimer = 0;
    motorStop(MOTOR_G);
  }
  if (kickTimer && time >= kickTimer) {
    kickTimer = 0;
    motorStop(MOTOR_K);
  }
  // Check motor rotary sensors
  checkMotors();
  // Read next command
  comm.readSerial();
}

void isReady() {
  /*
    Set grabber to default position and let the system know
    that the robot is ready to receive commands
   */
  ack(comm.next());
  closeGrabber();
}

// Actions
void move() {
  // ack(comm.next());
  
  // Arguments are the number of 'ticks' (15 deg increments) 
  // for each motor to travel. Sign determines direction.
  // Giving 0-value args will stop the corresponding motor(s)
  motorLDist = atoi(comm.next());
  //motorRDist = atoi(comm.next());
  if (motorLDist < 0) {
    motorLDir = -1;  // Bwd
    motorBackward(MOTOR_L, MOVE_PWR);
    motorForward(MOTOR_R, MOVE_PWR);
  } 
  else if (motorLDist > 0) {
    motorLDir = 1;  // Fwd
    motorForward(MOTOR_L, MOVE_PWR);
    motorBackward(MOTOR_R, MOVE_PWR);
  } 
  else { 
    motorLDir = 0;  // stopped
    motorStop(MOTOR_L);
    motorStop(MOTOR_R);
  }
  
  /*if (motorRDist < 0) {
    motorRDir = -1;
    motorBackward(MOTOR_R, MOVE_PWR);
  } 
  else if (motorRDist > 0) {
    motorRDir = 1;
    motorForward(MOTOR_R, MOVE_PWR);
  } 
  else {
    motorRDir = 0;
    motorStop(MOTOR_R);
  }*/
}

void closeGrabber() {
  ack(comm.next());
  if (grabberOpen && !grabTimer) {
    motorBackward(MOTOR_G, GRAB_POWER);
    grabberOpen = false;
    grabTimer = millis() + GRAB_TIME;
  }
}

void openGrabber() {
  ack(comm.next());
  if (!grabberOpen && !grabTimer) {
    motorForward(MOTOR_G, GRAB_POWER);
    grabberOpen = true;
    grabTimer = millis() + GRAB_TIME;
  }
}

void kick() {
  ack(comm.next());
  if (grabberOpen && !kickTimer) {
    motorForward(MOTOR_K, KICK_POWER);
    kickTimer = millis() + KICK_TIME;
  }
}

void checkMotors() {
  // Get sensor info from slave
  int bytesReceived = Wire.requestFrom(5, 1);
  int8_t motorLDiff = 0;
  //int8_t motorRDiff = 0;
  
  if (bytesReceived) {
    while (Wire.available()) motorLDiff = Wire.read();
    //if (Wire.available()) motorRDiff = Wire.read();
    // Update counters, test for completion     
    /// L update and completion test
    if (motorLDiff && motorLDir * (motorLDist -= motorLDiff) <= 0) {
      motorLDir = 0;
      motorStop(MOTOR_L);
      motorStop(MOTOR_R);
    }
    /// R update and completion test
    //if (motorRDiff && motorRDir * (motorRDist -= motorRDiff) <= 0) {
    //  motorRDir = 0;
    //  motorStop(MOTOR_R);
    //}
  }
}   

void ack(String ack_bit) {
  Serial.println(ack_bit);
  Serial.flush();  // force send
}

void invalidCommand(const char* command) {
  Serial.print("Invalid command: ");
  Serial.println(command);
}
