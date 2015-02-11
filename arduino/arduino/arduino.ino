/*
  Arduino code for SDP Group 7 2014
    
  This code assumes that clockwise is 'forward' for each motor, so please wire them up
  as such.
*/

#include <SDPArduino.h>
#include <SerialCommand.h>
#include <Wire.h>

// Motor numbers
#define MOTOR_FR 0
#define MOTOR_B 1
#define MOTOR_FL 2
#define MOTOR_KICK 3
#define MOTOR_GRAB 4

// Drive constants
#define MOVE_PWR 100
#define TURN_PWR 50
#define CRAWL_PWR 75

#define STRAFE_SIDE_F_POWER 70
#define STRAFE_SIDE_B_POWER 95
#define STRAFE_SIDE_OFFSET 20
#define STRAFE_SIDE_OFFSET 20

// Kicker and grabber constants
#define SHOOT_POWER 100
#define SHOOT_SWING_TIME 220

#define PASS_POWER 75
#define PASS_SWING_TIME 190

#define KICKER_RESET_POWER 100
#define KICKER_RESET_TIME 190
 
#define GRABBER_POWER 100
#define GRABBER_TIME 450

// Motor test constants
#define RUN_MOTORS_POWER 100
#define RUN_MOTORS_TIME 1000 // per direction

#define STOP_MOTORS_DELAY 150

// Command parser
SerialCommand comm;

// States
boolean grabber_open = false;
boolean kicker_ready = true;

void setup() {
  // Using library set up - it's fine
  SDPsetup();
  
  // Set up command action bindings
  comm.addCommand("FWD", forward);
  comm.addCommand("CRAWL_F", crawlForward);
  comm.addCommand("BACK", backward);
  comm.addCommand("CRAWL_B", crawlBackward);
  comm.addCommand("TURN_L", turnLeft);
  comm.addCommand("TURN_R", turnRight);
  comm.addCommand("ST_L", strafeL);
  comm.addCommand("ST_R", strafeR);
  comm.addCommand("ST_FL", strafeFL);
  comm.addCommand("ST_FR", strafeFR);
  comm.addCommand("ST_BL", strafeBL);
  comm.addCommand("ST_BR", strafeBR);
  comm.addCommand("GRAB", grabberToggle);
  comm.addCommand("O_GRAB", grabberOpen);
  comm.addCommand("C_GRAB", grabberClose);
  comm.addCommand("SHOOT", shoot);
  comm.addCommand("PASS", pass);
  comm.addCommand("STOP_D", stopDriveMotors);
  comm.addCommand("STOP_A", stopAllMotors);
  comm.addCommand("MOTORS", runDriveMotors);
  comm.setDefaultHandler(invalidCommand);

  Serial.println("<Ready>");
}

void loop() {
  comm.readSerial();
}


// Actions
void forward() {
  stopDriveMotors();
  motorForward(MOTOR_FL, MOVE_PWR);
  motorBackward(MOTOR_FR, MOVE_PWR);
}

void crawlForward() {
  stopDriveMotors();
  motorForward(MOTOR_FL, CRAWL_PWR);
  motorBackward(MOTOR_FR, CRAWL_PWR);
}

void backward() {
  stopDriveMotors();
  motorBackward(MOTOR_FL, MOVE_PWR);
  motorForward(MOTOR_FR, MOVE_PWR);
}

void crawlBackward() {
  stopDriveMotors();
  motorBackward(MOTOR_FL, CRAWL_PWR);
  motorForward(MOTOR_FR, CRAWL_PWR);
}

void strafeFL() {
  stopDriveMotors();
  motorBackward(MOTOR_FR, MOVE_PWR);
  motorForward(MOTOR_B, MOVE_PWR);
}

void strafeFR() {
  stopDriveMotors();
  motorForward(MOTOR_FL, MOVE_PWR);
  motorBackward(MOTOR_B, MOVE_PWR);
}

void strafeBL() {
  stopDriveMotors();
  motorBackward(MOTOR_FL, MOVE_PWR);
  motorForward(MOTOR_B, MOVE_PWR);
}

// TODO define constants (and tune)
void strafeL() {
  stopDriveMotors();
  motorBackward(MOTOR_FL, STRAFE_SIDE_F_POWER - STRAFE_SIDE_OFFSET - 1);
  motorBackward(MOTOR_FR, STRAFE_SIDE_F_POWER);
  motorForward(MOTOR_B, STRAFE_SIDE_B_POWER); 
}

// TODO define constants
void strafeR() {
  stopDriveMotors();
  motorForward(MOTOR_FR, STRAFE_SIDE_F_POWER - STRAFE_SIDE_OFFSET);
  motorForward(MOTOR_FL, STRAFE_SIDE_F_POWER);
  motorBackward(MOTOR_B, STRAFE_SIDE_B_POWER); 
}
void strafeBR() {
  stopDriveMotors();
  motorForward(MOTOR_FR, MOVE_PWR);
  motorBackward(MOTOR_B, MOVE_PWR);
}

void turnLeft() {
  stopDriveMotors();
  motorBackward(MOTOR_FL, TURN_PWR);
  motorBackward(MOTOR_FR, TURN_PWR);
  motorBackward(MOTOR_B, TURN_PWR);
}

void turnRight() {
  stopDriveMotors();
  motorForward(MOTOR_FL, TURN_PWR);
  motorForward(MOTOR_FR, TURN_PWR);
  motorForward(MOTOR_B, TURN_PWR);
}

void grabberToggle() {
  if (!grabber_open) {
    grabberOpen();
  } else {
    grabberClose();
  }
}

void grabberClose() {
  if (grabber_open && kicker_ready) {
    motorBackward(MOTOR_GRAB, GRABBER_POWER);
    grabber_open = false;
    delay(GRABBER_TIME);
    motorStop(MOTOR_GRAB);
  }
}

void grabberOpen() {
  if (!grabber_open) {
    motorForward(MOTOR_GRAB, GRABBER_POWER);
    grabber_open = true;
    delay(GRABBER_TIME);
    motorStop(MOTOR_GRAB);
  }
}

void pass() {
  if (kicker_ready && grabber_open) {
    kicker_ready = false;
    motorBackward(MOTOR_KICK, PASS_POWER);
    delay(PASS_SWING_TIME);
    motorStop(MOTOR_KICK);
    resetKicker();
  }
}

void shoot() {
  if (kicker_ready && grabber_open) {
    kicker_ready = false;
    motorBackward(MOTOR_KICK, SHOOT_POWER);
    delay(SHOOT_SWING_TIME);
    motorStop(MOTOR_KICK);
    resetKicker();
  }
}

void resetKicker() {
  if (!kicker_ready && grabber_open) {
    delay(100);
    motorForward(MOTOR_KICK, KICKER_RESET_POWER);
    delay(KICKER_RESET_TIME);
    motorStop(MOTOR_KICK);
    kicker_ready = true;
  }
  else {
    grabberOpen();
    resetKicker();
  }
}

void runDriveMotors() {
  Serial.println("Running the drive motors forward (clockwise)");
  motorForward(MOTOR_FL, RUN_MOTORS_POWER);
  motorForward(MOTOR_B, RUN_MOTORS_POWER);
  motorForward(MOTOR_FR, RUN_MOTORS_POWER);
  delay(RUN_MOTORS_TIME);
  stopDriveMotors();
  
  Serial.println("Running the drive motors backward (anti-clockwise)");
  motorBackward(MOTOR_FL, RUN_MOTORS_POWER);
  motorBackward(MOTOR_B, RUN_MOTORS_POWER);
  motorBackward(MOTOR_FR, RUN_MOTORS_POWER);
  delay(RUN_MOTORS_TIME);
  stopDriveMotors();
}

void stopDriveMotors() {
  motorStop(MOTOR_FL);
  motorStop(MOTOR_B);
  motorStop(MOTOR_FR);
  delay(STOP_MOTORS_DELAY);
}

void stopAllMotors() {
  motorAllStop();
  delay(STOP_MOTORS_DELAY);
}
void invalidCommand(const char* command) {}
