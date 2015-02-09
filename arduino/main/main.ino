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
#define MOVE_PWR 75
#define TURN_PWR 30
#define CRAWL_PWR 30

// Kicker and grabber constants
#define SHOOT_POWER 100
#define SHOOT_SWING_TIME 255

#define PASS_POWER 60
#define PASS_SWING_TIME 180

#define KICKER_RESET_POWER 60
#define KICKER_RESET_TIME 150

#define GRABBER_POWER 100
#define GRABBER_TIME 800

// Motor test constants
#define RUN_MOTORS_POWER 100
#define RUN_MOTORS_TIME 1000 // per direction

#define STOP_MOTORS_DELAY 100

SerialCommand comm;

// States
boolean grabber_open = false;
boolean kicker_ready = true;

void setup() {
  SDPsetup();
  comm.addCommand("FWD", forward);
  comm.addCommand("CRAWL", crawl);
  comm.addCommand("BACK", backward);
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
  motorBackward(MOTOR_FR, MOVE_PWR);
  motorForward(MOTOR_FL, MOVE_PWR);
}

void crawl() {
  stopDriveMotors();
  motorBackward(MOTOR_FR, CRAWL_PWR);
  motorForward(MOTOR_FL, CRAWL_PWR);
}

void backward() {
  stopDriveMotors();
  motorForward(MOTOR_FR, MOVE_PWR);
  motorBackward(MOTOR_FL, MOVE_PWR);
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

void strafeL() {
  stopDriveMotors();
  motorBackward(MOTOR_FL,70);
  motorBackward(MOTOR_FR,70);
  motorForward(MOTOR_B,100); 
}

void strafeR() {
  stopDriveMotors();
  motorForward(MOTOR_FL,70);
  motorForward(MOTOR_FR,70);
  motorBackward(MOTOR_B,100); 
}
void strafeBR() {
  stopDriveMotors();
  motorForward(MOTOR_FR, MOVE_PWR);
  motorBackward(MOTOR_B, MOVE_PWR);
}

void turnLeft() {
  stopDriveMotors();
  motorBackward(MOTOR_FR, TURN_PWR);
  motorBackward(MOTOR_B, TURN_PWR);
  motorBackward(MOTOR_FL, TURN_PWR);
}

void turnRight() {
  stopDriveMotors();
  motorForward(MOTOR_FR, TURN_PWR);
  motorForward(MOTOR_B, TURN_PWR);
  motorForward(MOTOR_FL, TURN_PWR);
}

void grabberToggle() {
  if (!grabber_open) {
    grabberOpen();
  } else {
    grabberClose();
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

void grabberClose() {
  if (grabber_open) {
    motorBackward(MOTOR_GRAB, GRABBER_POWER);
    grabber_open = false;
    delay(GRABBER_TIME);
    motorStop(MOTOR_GRAB);
  }
}

void pass() {
  if (kicker_ready) {
    kicker_ready = false;
    motorForward(MOTOR_KICK, PASS_POWER);
    delay(PASS_SWING_TIME);
    motorStop(MOTOR_KICK);
    resetKicker();
  }
}

void shoot() {
  if (kicker_ready) {
    kicker_ready = false;
    motorForward(MOTOR_KICK, SHOOT_POWER);
    delay(SHOOT_SWING_TIME);
    motorStop(MOTOR_KICK);
    resetKicker();
  }
}

void resetKicker() {
  if (!kicker_ready) {
    motorBackward(MOTOR_KICK, KICKER_RESET_POWER);
    delay(KICKER_RESET_TIME);
    motorStop(MOTOR_KICK);
    kicker_ready = true;
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
