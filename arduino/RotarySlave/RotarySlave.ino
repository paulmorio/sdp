#include <Rotary.h>
#include <Wire.h>

#define ROTARY_SLAVE_ADDRESS 5
#define ROTARY_COUNT 2

Rotary sensors[] = {Rotary(0, 1), Rotary(3, 2)};

byte diffs[ROTARY_COUNT] = {0};

void setup() {
  Wire.begin(ROTARY_SLAVE_ADDRESS);
  Wire.onRequest(sendDiffs);
}

void loop() {
  updateDiffs();
}

void updateDiffs() {
  for (int i = 0; i < sizeof(diffs); i++) {
    byte result = sensors[i].process();
    if (result == DIR_CW) diffs[i]++;
    else if (result == DIR_CCW) diffs[i]--;
  }
}

void sendDiffs() {
  Wire.write(diffs, sizeof(diffs));
  memset(diffs, 0, sizeof(diffs));
}
