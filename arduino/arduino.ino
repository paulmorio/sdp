/*
  Simple arduino code to accompany initial java communicator.
  
  This sketch parses an integer from serial then returns its successor,
  merely a ping test.
  
  Author: Chris Seaton
*/

void setup() {
  // initialize digital pin 13 as an output.
  Serial.begin(9600);
  Serial.println("<Arduino is ready>");
}

void loop() {
  while (Serial.available() > 0) {
    int in = Serial.parseInt();
    Serial.println(in + 1);
  }
}
