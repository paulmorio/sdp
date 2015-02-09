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

#define RUN_MOTORS_POWER 100
#define RUN_MOTORS_TIME 1000 // per direction

#define MOVE_PWR 100
#define TURN_PWR 100

SerialCommand comm;

void setup() {
  SDPsetup();
  comm.addCommand("FWD", forward);
  comm.addCommand("BACK", backward);
  comm.addCommand("ST_FL", strafe_fl);
  comm.addCommand("ST_FR", strafe_fr);
  comm.addCommand("ST_BL", strafe_bl);
  comm.addCommand("ST_BR", strafe_br);
  comm.addCommand("TURN_L", turn_left);
  comm.addCommand("TURN_R", turn_right);
  comm.addCommand("GRABOPEN", grabopen);
  comm.addCommand("GRABCLOSE", grabclose);
  comm.addCommand("KICK", kick);
  comm.addCommand("MOTORS", run_drive_motors);
  comm.addCommand("STOP", stop_drive_motors);
  comm.addCommand("STRAFE_R", strafe_r);
  comm.addCommand("STRAFE_L", strafe_l);
  
  comm.setDefaultHandler(invalid_command);

  Serial.println("<Ready>");
}

void loop() {
  comm.readSerial();
}


// Actions
void forward() {
  stop_drive_motors();
  motorBackward(MOTOR_FR, MOVE_PWR);
  motorForward(MOTOR_FL, MOVE_PWR);
  Serial.println("Moving forward");
}

void backward() {
  stop_drive_motors();
  motorForward(MOTOR_FR, MOVE_PWR);
  motorBackward(MOTOR_FL, MOVE_PWR);
  Serial.println("Moving backward");
}

void strafe_fl() {
  stop_drive_motors();
  motorBackward(MOTOR_FR, MOVE_PWR);
  motorForward(MOTOR_B, MOVE_PWR);
  Serial.println("Strafing forward-left");
}

void strafe_fr() {
  stop_drive_motors();
  motorForward(MOTOR_FL, MOVE_PWR);
  motorBackward(MOTOR_B, MOVE_PWR);
  Serial.println("Strafing forward-right");
}

void strafe_bl() {
  stop_drive_motors();
  motorBackward(MOTOR_FL, MOVE_PWR);
  motorForward(MOTOR_B, MOVE_PWR);
  Serial.println("Strafing back-left");
}

void strafe_l() {
  stop_drive_motors();
  motorBackward(MOTOR_FL,70);
  motorBackward(MOTOR_FR,70);
  motorForward(MOTOR_B,100); 
}

void strafe_r() {
  stop_drive_motors();
  motorForward(MOTOR_FL,70);
  motorForward(MOTOR_FR,70);
  motorBackward(MOTOR_B,100); 
}
void strafe_br() {
  stop_drive_motors();
  motorForward(MOTOR_FR, MOVE_PWR);
  motorBackward(MOTOR_B, MOVE_PWR);
  Serial.println("Strafing back-right");
}

void turn_left() {
  stop_drive_motors();
  motorBackward(MOTOR_FR, TURN_PWR);
  motorBackward(MOTOR_B, TURN_PWR);
  motorBackward(MOTOR_FL, TURN_PWR);

  Serial.println("Turning left");
}

void L45() {
 stop_drive_motors();
  motorBackward(MOTOR_FR, TURN_PWR);
  motorBackward(MOTOR_B, TURN_PWR);
  motorBackward(MOTOR_FL, TURN_PWR);
  delay(180);
  stop_drive_motors();
  
}
void turn_right() {
  stop_drive_motors();
  motorForward(MOTOR_FR, TURN_PWR);
  motorForward(MOTOR_B, TURN_PWR);
  motorForward(MOTOR_FL, TURN_PWR);

  Serial.println("Turning right");
}

void grabopen() {
    stop_drive_motors();
    motorForward(4,100);
    delay(800);
    stop_drive_motors();
    Serial.println("Grabbed");
}

void grabclose() {
    stop_drive_motors();
    motorBackward(4,100);
    delay(800);
    stop_drive_motors();
    Serial.println("Grabbed");
}

void kick() {
    motorForward(MOTOR_KICK, 100);
    delay(500);
    stop_drive_motors();
    delay(20);
    motorBackward(MOTOR_KICK,60);
    delay(150);
    stop_drive_motors();
    Serial.println("Kicked");
}

void run_drive_motors() {
  Serial.println("Running the drive motors forward (clockwise)");
  motorForward(MOTOR_FL, RUN_MOTORS_POWER);
  motorForward(MOTOR_B, RUN_MOTORS_POWER);
  motorForward(MOTOR_FR, RUN_MOTORS_POWER);
  delay(RUN_MOTORS_TIME);
  stop_drive_motors();
  
  Serial.println("Running the drive motors backward (anti-clockwise)");
  motorBackward(MOTOR_FL, RUN_MOTORS_POWER);
  motorBackward(MOTOR_B, RUN_MOTORS_POWER);
  motorBackward(MOTOR_FR, RUN_MOTORS_POWER);
  delay(RUN_MOTORS_TIME);
  stop_drive_motors();
}

void stop_drive_motors() {
  motorStop(MOTOR_FL);
  motorStop(MOTOR_B);
  motorStop(MOTOR_FR);
  motorStop(MOTOR_KICK);
  motorStop(4);
}

void invalid_command(const char* command) {}
