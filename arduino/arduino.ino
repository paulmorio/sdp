#include <SDPArduino.h>
#include <SerialCommand.h>
#include <Wire.h>

/*
  Arduino code for SDP Group 7 2014
  
  Author: Chris Seaton
  
  Motor numbers are to be finalized:
    FL: 0
    FR: 1
    RL: 2
    RR: 3
    Grabber: 4
    Kicker: 5
*/

// Communications
SerialCommand comm;
int GRABBER_OPEN = 0;

void setup() {
  
  SDPsetup()  // Using included setup for now  
  
  comm.addCommand("A_KICK", kick);
  comm.addCommand("A_GRAB", grab);
  comm.addCommand("A_L_ST", strafe_left);
  comm.addCommand("A_R_ST", strafe_right);
  comm.addCommand("A_FWD", forward);
  comm.addCommand("A_BK", backward);
  comm.addCommand("A_TL_90", turn_left_90);
  comm.addCommand("A_TR_90", turn_right_90);
  comm.addCommand("A_MTR", run_motors);
  comm.setDefaultHandler(invalid_command);
  
  Serial.println("<Ready>");
}

void loop() {
  comm.readSerial();
}

// Skeletal code for basic actions
void kick() {
  Serial.println("Kicked!");
}

void grab() { // toggle
  if (GRABBER_OPEN){
    Serial.println("Grabber closed");
  } else {
    Serial.println("Grabber opened");
  }
}

void strafe_left() {
  Serial.println("Strafing left");
}

void strafe_right() {
  Serial.println("Strafing right");
}

void forward() {
  Serial.println("Moving forward");
}

void backward() {
  Serial.println("Moving backward");
}

void turn_left_90() {
  Serial.println("Turning left 90deg");
}

void turn_right_90() {
  Serial.println("Turning right 90deg");
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
