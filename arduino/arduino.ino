/*
  Simple arduino code to accompany initial java communicator.
  
  This sketch parses an integer from serial then returns its successor,
  merely a ping test.
  
  Author: Chris Seaton
*/

void setup() {
  digitalWrite(8, HIGH);  // enable RF
  Serial.begin(115200);  // default baudrate for SRF
  Serial.println("<Arduino is ready>");
}

void loop() {
  while (Serial.available() > 0) {
    int in = Serial.parseInt();
    Serial.write(in);  // write input back to serial - for testing
  }
}
