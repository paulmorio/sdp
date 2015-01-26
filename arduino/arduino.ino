#include <SDPArduino.h>
#include <SerialCommand.h>
#include <Wire.h>

/*
  Arduino code for SDP Group 7 2014
  
  Author: Chris Seaton
  
  Motor numbers are to be finalized:
    F: 0
    R: 1
    B: 2
    L: 3
    Kicker: 4
    Grabber: 5
    
  This code assumes that clockwise is 'forward'.
*/

// Communications
SerialCommand comm;
int GRABBER_OPEN = 0;

void setup() {
  
  SDPsetup();  // Using included setup for now  
  
  comm.addCommand("KICK", kick);
  comm.addCommand("GRAB", grab);
  comm.addCommand("ST_L", strafe_left);
  comm.addCommand("ST_R", strafe_right);
  comm.addCommand("FWD", forward);
  comm.addCommand("BACK", backward);
  comm.addCommand("TURN_L", turn_left);
  comm.addCommand("TURN_R", turn_right);
  comm.addCommand("MOTORS", run_motors);
  comm.addCommand("STOP", motorAllStop);
  comm.setDefaultHandler(invalid_command);
  
  Serial.println("<Ready>");
}

void loop() {
  comm.readSerial();
}

// Skeletal code for basic actions
void kick() {
  motorForward(4, 100);
  delay(100);
  motorStop(4);
}

void grab() { // toggle
  if (GRABBER_OPEN){
    Serial.println("Grabber closed");
  } else {
    Serial.println("Grabber opened");
  }
}

void strafe_left() {
  motorAllStop();
  motorForward(0, 100);
  motorBackward(2, 100);
  Serial.println("Strafing left");
}

void strafe_right() {
  motorAllStop();
  motorBackward(0, 100);
  motorForward(2, 100);
  Serial.println("Strafing right");
}

void forward() {
  Serial.println("Moving forward");
  motorAllStop();
  motorBackward(1, 100);
  motorForward(3, 100);
}

void backward() {
  Serial.println("Moving backward");
  motorAllStop();
  motorForward(1, 100);
  motorBackward(3, 100);
}

void turn_left() {
  motorAllStop();
  motorForward(0, 100);
  motorForward(1, 100);
  motorForward(2, 100);
  motorForward(3, 100);
  Serial.println("Turning left");
}

void turn_right() {
  motorAllStop();
  motorBackward(0, 100);
  motorBackward(1, 100);
  motorBackward(2, 100);
  motorBackward(3, 100);
  Serial.println("Turning right");
}

void run_motors() {
  Serial.println("Briefly running the motors");
  motorForward(0, 50);
  motorForward(1, 50);
  motorForward(2, 50);
  motorForward(3, 50);
  motorForward(4, 50);
  motorForward(5, 50);
  delay(2500);
  motorAllStop();
}

void invalid_command(const char* command) {}
