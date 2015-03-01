#include <Rotary.h>
#include <Wire.h>

#define ROTARY_SLAVE_ADDRESS 5
#define ROTARY_COUNT 2
#define SENSOR_COUNT 1

Rotary rotarySensors[] = {Rotary(0, 1), Rotary(3, 2)};
int grabberSwitchPin = 11;
byte readings[ROTARY_COUNT + SENSOR_COUNT] = {0};

void setup() {
  pinMode(grabberSwitchPin, INPUT);
  Wire.begin(ROTARY_SLAVE_ADDRESS);
  Wire.onRequest(sendReadings);
}

void loop() {
  readings[2] = digitalRead(grabberSwitchPin);
  updateDiffs();
}

void updateDiffs() {
  for (int i = 0; i < ROTARY_COUNT; i++) {
    byte result = rotarySensors[i].process();
    if (result == DIR_CW) readings[i]++;
    else if (result == DIR_CCW) readings[i]--;
  }
}

void sendReadings() {
  Wire.write(readings, sizeof(readings));
  memset(readings, 0, sizeof(readings));
}
