/*
  Arduino code for SDP Group 7 2014
    
  This code assumes that clockwise is 'forward' for each motor, so please wire them up
  as such.
*/

#include <SDPArduino.h>
#include <SerialCommand.h>
#include <Wire.h>

// Motor numbers
#define MOTOR_F 0
#define MOTOR_B 1
#define MOTOR_K 2
#define MOTOR_G 4

#define RUN_MOTORS_POWER 100
#define RUN_MOTORS_TIME 1000 // per direction

#define MOVE_PWR 100
#define TURN_PWR 100

SerialCommand comm;

void setup() {
  SDPsetup();
  comm.addCommand("FWD", forward);
  comm.addCommand("BACK", backward);
  comm.addCommand("TURN_L", turn_left);
  comm.addCommand("TURN_R", turn_right);
  comm.addCommand("GRAB", grab);
  comm.addCommand("KICK", kick);
  comm.addCommand("STOP", stop_drive_motors);
  comm.setDefaultHandler(invalid_command);

  Serial.println("<Ready>");
}

void loop() {
  comm.readSerial();
}


// Actions
void forward() {
  stop_drive_motors();
  motorForward(MOTOR_F, MOVE_PWR);
  Serial.println("Moving forward");
}

void backward() {
  stop_drive_motors();
  motorBackward(MOTOR_F, MOVE_PWR);
  Serial.println("Moving backward");
}

void turn_left() {
  stop_drive_motors();
  motorBackward(MOTOR_B, TURN_PWR);
  Serial.println("Turning left");
}

void turn_right() {
  stop_drive_motors();
  motorForward(MOTOR_B, TURN_PWR);
  Serial.println("Turning right");
}

void grab() {
    Serial.println("Grabbed");
}

void kick() {
    Serial.println("Kicked");
}

void stop_drive_motors() {
  motorStop(MOTOR_F);
  motorStop(MOTOR_B);
  delay(100);
}

void invalid_command(const char* command) {}
