

#include <Rotary.h>
#include <Wire.h>

Rotary r = Rotary(0, 1);
Rotary t = Rotary(4, 5);
int temp = 0;
int temp2 =0;
 int lookup[] = {0, 15, 30, 45, 60,75, 90, 105, 120 , 135, 150, 165, 180, 195 , 210 , 225, 240 , 255 , 270  ,285 , 300  , 315 , 330 , 345  , 360};

void setup() {
  Serial.begin(9600);
  Serial.println("Hello");
  // Starts i2C on bus number 2 
  Wire.begin(5);
  Wire.onRequest(requestEvent);
}

void loop() {
  unsigned char result = r.process();
  unsigned char resultt = t.process();
  if (result) {
    //Serial.println(result == DIR_CW ? "Right" : "Left");
    result == DIR_CW ? temp = temp - 1 : temp = temp + 1 ;
    
    if (temp == -1 ) {
      temp = 24;
    } 
    if (temp == 25) {
      temp = 0;
    }
    
    
    Serial.print( lookup[temp]); 
    Serial.println (" Degrees - Motor 1");  
   
   
    
  }
  
  
  //excuse the var names, quick and dirty to test it working whilst polling 2 sensors at the same time.
   if (resultt) {
    //Serial.println(result == DIR_CW ? "Right" : "Left");
    resultt == DIR_CW ? temp2 = temp2 - 1 : temp2 = temp2 + 1 ;
    
    if (temp2 == -1 ) {
      temp2 = 24;
    } 
    if (temp2 == 25) {
      temp2 = 0;
    }
    
    
    Serial.print( lookup[temp2]); 
    Serial.println (" Degrees - Motor 2");  
   
   
    
  }
}

void requestEvent() {
 Wire.write(temp); 
  
}


