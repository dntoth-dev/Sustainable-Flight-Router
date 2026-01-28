#include <SoftwareSerial.h>
#include <Wire.h> 
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27,20,4);  // set the LCD address to 0x27 for a 16 chars and 2 line display
SoftwareSerial mySerial(10, 11);

void setup()
{
  lcd.init();   
  Serial.begin(9600);
  mySerial.begin(9600);  // set
  lcd.setCursor(0,0); // set cursor pos
  
}

void loop()
{
  while (mySerial.available()){
    int bytes = mySerial.read();
    char c = bytes;
    Serial.print(c);
  }
}