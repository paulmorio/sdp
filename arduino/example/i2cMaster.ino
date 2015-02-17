


#include <Wire.h>

void setup()
{
  Wire.begin();        // join i2c bus (address optional for master)
  Serial.begin(9600);  // start serial for output
}

void loop()
{
  Wire.requestFrom(5, 1);    // request 6 bytes from slave device #2
  
  while (Wire.available())   // slave may send less than requested
  {
    byte c = Wire.read(); // receive a byte as character
    Serial.println(c, DEC);         // print the character
  }

  delay(15);
}
