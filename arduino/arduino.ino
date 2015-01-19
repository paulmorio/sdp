#include <SerialCommand.h>

/*
  Arduino code for SDP Group 7 2014
  
  Author: Chris Seaton
*/

// Communications
SerialCommand comm;

void setup() {
  // Set RF pin and select radio
  pinMode(8, OUTPUT);
  digitalWrite(8, HIGH);
  // Set LED pin
  pinMode(13, OUTPUT);
  
  // Init serial at default SRF baudrate
  Serial.begin(115200);
  
  comm.addCommand("A_KICK", kick);
  comm.addCommand("A_PUNCH", punch);
  comm.setDefaultHandler(invalid_command);
  
  Serial.println("<Arduino is ready>");
}

void loop() {
  comm.readSerial();
}

void kick() {
  digitalWrite(13, HIGH);
  Serial.println("Kicked!");
}

void punch() {
  digitalWrite(13, LOW);
  Serial.println("Punched!");
}

void invalid_command(const char* command) {}
