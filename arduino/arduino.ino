#include <SerialCommand.h>

/*
  Arduino code for SDP Group 7 2014
  
  Author: Chris Seaton
*/

// Communications
SerialCommand comm;
int GRABBER_OPEN = 0;

void setup() {
  // Set RF pin and select radio
  pinMode(8, OUTPUT);
  digitalWrite(8, HIGH);
  // Set LED pin
  pinMode(13, OUTPUT);
  
  // Init serial at default SRF baudrate
  Serial.begin(115200);
  
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
}

void invalid_command(const char* command) {}
