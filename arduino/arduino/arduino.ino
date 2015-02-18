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
#define MOTOR_KICK 4
#define MOTOR_GRAB 5

#define MOVE_PWR 100

// Kicker and grabber constants
#define KICK_POWER 100
#define KICK_TIME 200
 
#define GRABBER_POWER 100
#define GRABBER_TIME 220

// Command parser
SerialCommand comm;

// States and counters
boolean grabber_open = false;
boolean kicker_ready = true;
boolean motorLMoving = false;
int motorLDist = 0;
boolean motorRMoving = false;
int motorRDist = 0;

void setup() {
  // Using library set up - it's fine
  SDPsetup();
  
  // Set up command action bindings
  comm.addCommand("MOVE", move);
  comm.addCommand("O_GRAB", grabberOpen);
  comm.addCommand("C_GRAB", grabberClose);
  comm.addCommand("GRAB", grabberToggle);
  comm.addCommand("KICK", kick);
  comm.addCommand("READY", isReady);
  comm.setDefaultHandler(invalidCommand);
}

void loop() {
  // Check motor counters and stop if expired
  checkMotors();
  // Read and perform next command from serial if available
  comm.readSerial();
}

void isReady() {
  /*
    Set grabber to default position and let the system know
    that the robot is ready to receive commands
   */
  ack(comm.next());
  grabberClose();
}

// Actions
void move() {
  ack(comm.next());
  
  // Arguments are the number of 'ticks' (15 deg increments) 
  // for each motor to travel. Sign determines direction.
  // Giving 0 args will explicitly stop the corresponding motor(s)
  motorLDist = atoi(comm.next());
  motorRDist = atoi(comm.next());

  if (motorLDist < 0) {  // Backward - dist is neg
    motorLMoving = true;
    motorLDist = -motorLDist;
    motorBackward(MOTOR_L, MOVE_PWR);
  } else if (motorLDist > 0) {  // Forward - dist is pos
    motorLMoving = true;
    motorForward(MOTOR_L, MOVE_PWR);
  } else {  // Stop - dist is 0
    motorStop(MOTOR_L);
  }
  
  if (motorRDist < 0) {  // Backward - dist is neg
    motorRMoving = true;
    motorRDist = -motorRDist;
    motorBackward(MOTOR_R, MOVE_PWR);
  } else if (motorRDist > 0) {  // Forward - dist is pos
    motorRDist = true;
    motorForward(MOTOR_R, MOVE_PWR);
  } else {  // Stop - dist is 0
    motorStop(MOTOR_R);
  }
}

void grabberToggle() {
  if (grabber_open) {
    grabberClose();
  } else {
    grabberOpen();
  }
}

void grabberClose() {
  ack(comm.next());
  if (grabber_open) {
    motorBackward(MOTOR_GRAB, GRABBER_POWER);
    grabber_open = false;
    delay(GRABBER_TIME);
    motorStop(MOTOR_GRAB);
  }
}

void grabberOpen() {
  ack(comm.next());
  if (!grabber_open) {
    motorForward(MOTOR_GRAB, GRABBER_POWER);
    grabber_open = true;
    delay(GRABBER_TIME);
    motorStop(MOTOR_GRAB);
  }
}

void kick() {
  ack(comm.next());
  if (grabber_open) {
    motorBackward(MOTOR_KICK, 100);
    delay(50);
    motorForward(MOTOR_KICK, 100);
    delay(200);
    motorStop(MOTOR_KICK);
  }
}

void checkMotors() {
  // Get sensor info from slave
  int bytesReceived = Wire.requestFrom(5, 2, true);
  if (bytesReceived) {
      int motorLDiff = Wire.read();
      int motorRDiff = Wire.read();
      delay(1000);
      Serial.println(motorLDiff);
      Serial.println(motorRDiff);
      // Update counters, test for completion
      /// L update and completion test
      if (motorLMoving && (motorLDist -= motorLDiff) <= 0) {
          motorLMoving = false;
          motorStop(MOTOR_L);
      }
      /// R update and completion test
      if (motorRMoving && (motorRDist -= motorRDiff) <= 0) {
          motorRMoving = false;
          motorStop(MOTOR_R);  
      }
  }
}   

void ack(String ack_bit) {
  Serial.println(ack_bit);
  Serial.flush();  // force send
}

void invalidCommand(const char* command) {}
