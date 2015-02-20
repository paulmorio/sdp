/*
 * Rotary encoder slave board sample code to be used with the accompanying
 * master board sample code.
 * This sketch will poll the rotary encoders and record movement steps in
 * the diffs array. This diffs array, on request, is sent on the I2C bus
 * and is then reset.
 *
 * Author: Chris Seaton, SDP Group 7 2015
 */

#include <Rotary.h>
#include <Wire.h>

#define ROTARY_SLAVE_ADDRESS 5
#define ROTARY_COUNT 6

// If the I2C ports are at 12 o'clock then these assignments correspond to ports 
// starting from top-left (11 o'clock) then in counter-clockwise sequence
Rotary sensors[] = {
  Rotary(0, 1), Rotary(3, 2), Rotary(5, 6),
  Rotary(8, 7), Rotary(9, 10), Rotary(12, 11)
};

// Keep track of differences since the master last polled
byte diffs[ROTARY_COUNT] = {0};

void setup() {
  Wire.begin(ROTARY_SLAVE_ADDRESS);  // I2C slave at given address
  Wire.onRequest(sendDiffs);  // Run given method when bits are requested
}

void loop() {
  updateDiffs();
}

void updateDiffs() {
  // Read sensors and update the diffs accordingly
  for (int i = 0; i < sizeof(diffs); i++) {
    byte result = sensors[i].process();  // Get sensor i reading
    if (result == DIR_CW) diffs[i]++;   // Increment if clockwise step
    else if (result == DIR_CCW) diffs[i]--;  // Decrement if counter-clockwise
  }
}

void sendDiffs() {
  // Send the diffs over the wire then reset
  Wire.write(diffs, sizeof(diffs)); // Send diffs to master
  memset(diffs, 0, sizeof(diffs));  // Set diffs to zero
}
