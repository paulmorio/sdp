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
#define MOTOR_R 1
#define MOTOR_B 2
#define MOTOR_L 3
#define MOTOR_K 4
#define DRIVE_RESET_DELAY 100
#define VEER_OFFSET 5

#define RUN_MOTORS_POWER 50
#define RUN_MOTORS_TIME 1000 // per direction
// Kick timing
#define KICK_LENGTH 200
#define KICK_POWER 100
#define KICK_STOP_DELAY 300
#define KICK_RESET_DELAY 200
#define KICK_RESET_POWER 50

#define MOVE_PWR_2WD 100 // for testing
#define MOVE_PWR_4WD 75
#define TURN_PWR 25

SerialCommand comm;

void setup() {
  SDPsetup();
  comm.addCommand("KICK", kick);
  comm.addCommand("ST_L", strafe_left);
  comm.addCommand("ST_R", strafe_right);
  comm.addCommand("FWD", forward);
  comm.addCommand("BACK", backward);
  comm.addCommand("TURN_L", turn_left);
  comm.addCommand("TURN_R", turn_right);
  comm.addCommand("MOTORS", run_drive_motors);
  comm.addCommand("STOP", stop_drive_motors);
  comm.addCommand("ST_FL", strafe_fl);
  comm.addCommand("ST_FR", strafe_fr);
  comm.addCommand("ST_BL", strafe_bl);
  comm.addCommand("ST_BR", strafe_br);
  comm.setDefaultHandler(invalid_command);
  
  Serial.println("<Ready>");
}

void loop() {
  comm.readSerial();
}


// Actions
void kick() {
  // Kick
  motorBackward(MOTOR_K, KICK_POWER);
  delay(KICK_LENGTH);  // length of kick
  Serial.println("Kicked");
  motorStop(MOTOR_K);
  delay(KICK_STOP_DELAY); // motor cool-off
  // Reset kicker
  motorForward(MOTOR_K, KICK_RESET_POWER);
  delay(KICK_RESET_DELAY);  // reset time
  motorStop(MOTOR_K);  // Shouldn't need a cool off unless kicking immediately after
  Serial.println("Kicker reset");
}

void strafe_left() {
  stop_drive_motors();
  motorForward(MOTOR_B, MOVE_PWR_2WD - VEER_OFFSET);
  motorBackward(MOTOR_F, MOVE_PWR_2WD);
  Serial.println("Strafing left");
}

void strafe_right() {
  stop_drive_motors();
  motorBackward(MOTOR_B, MOVE_PWR_2WD);
  motorForward(MOTOR_F, MOVE_PWR_2WD - VEER_OFFSET);
  Serial.println("Strafing right");
}

void strafe_fl() {
  stop_drive_motors();
  motorBackward(MOTOR_F, MOVE_PWR_4WD);
  motorBackward(MOTOR_R, MOVE_PWR_4WD);
  motorForward(MOTOR_B, MOVE_PWR_4WD);
  motorForward(MOTOR_L, MOVE_PWR_4WD);
  Serial.println("Strafing FL");
}

void strafe_fr() {
  stop_drive_motors();
  motorForward(MOTOR_F, MOVE_PWR_4WD);
  motorBackward(MOTOR_R, MOVE_PWR_4WD);
  motorBackward(MOTOR_B, MOVE_PWR_4WD);
  motorForward(MOTOR_L, MOVE_PWR_4WD);
  Serial.println("Strafing FR");
}

void strafe_bl() {
  stop_drive_motors();
  motorBackward(MOTOR_F, MOVE_PWR_4WD);
  motorForward(MOTOR_B, MOVE_PWR_4WD);
  motorBackward(MOTOR_L, MOVE_PWR_4WD);
  motorForward(MOTOR_R, MOVE_PWR_4WD);
  Serial.println("Strafing BL");
}

void strafe_br() {
  stop_drive_motors();
  motorForward(MOTOR_F, MOVE_PWR_4WD);
  motorBackward(MOTOR_B, MOVE_PWR_4WD);
  motorForward(MOTOR_R, MOVE_PWR_4WD);
  motorBackward(MOTOR_L, MOVE_PWR_4WD);
}

void forward() {
  stop_drive_motors();
  motorBackward(MOTOR_R, MOVE_PWR_2WD - VEER_OFFSET);
  motorForward(MOTOR_L, MOVE_PWR_2WD);
  Serial.println("Moving forward");
}

void backward() {
  stop_drive_motors();
  motorForward(MOTOR_R, MOVE_PWR_2WD);
  motorBackward(MOTOR_L, MOVE_PWR_2WD - VEER_OFFSET);
  Serial.println("Moving backward");
}

void turn_left() {
  stop_drive_motors();
  motorBackward(MOTOR_F, TURN_PWR);
  motorBackward(MOTOR_R, TURN_PWR);
  motorBackward(MOTOR_B, TURN_PWR);
  motorBackward(MOTOR_L, TURN_PWR);
  Serial.println("Turning left");
}

void turn_right() {
  stop_drive_motors();
  motorForward(MOTOR_F, TURN_PWR);
  motorForward(MOTOR_R, TURN_PWR);
  motorForward(MOTOR_B, TURN_PWR);
  motorForward(MOTOR_L, TURN_PWR);
  Serial.println("Turning right");
}

void run_drive_motors() {
  Serial.println("Running the drive motors forward");
  stop_drive_motors();
  motorForward(MOTOR_F, RUN_MOTORS_POWER);
  motorForward(MOTOR_R, RUN_MOTORS_POWER);
  motorForward(MOTOR_B, RUN_MOTORS_POWER);
  motorForward(MOTOR_L, RUN_MOTORS_POWER);
  delay(RUN_MOTORS_TIME);
  stop_drive_motors();
  Serial.println("Running the drive motors backward");
  motorBackward(MOTOR_F, RUN_MOTORS_POWER);
  motorBackward(MOTOR_R, RUN_MOTORS_POWER);
  motorBackward(MOTOR_B, RUN_MOTORS_POWER);
  motorBackward(MOTOR_L, RUN_MOTORS_POWER);
  delay(RUN_MOTORS_TIME);
  stop_drive_motors();
}

void stop_drive_motors() {
  motorStop(MOTOR_F);
  motorStop(MOTOR_R);
  motorStop(MOTOR_B);
  motorStop(MOTOR_L);
  delay(DRIVE_RESET_DELAY);
}

void invalid_command(const char* command) {}
