#include <SoftwareSerial.h>
#include <Wire.h> 
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 20, 4); 
SoftwareSerial mySerial(10, 11);

String tempdata;
String route;
String default_routes[5]; // maximum number of routes is 5

void setup() {
  lcd.init();   
  lcd.backlight();
  Serial.begin(9600);
  mySerial.begin(9600);  
  
  lcd.setCursor(0,0);
  lcd.print("Waiting for data...");
}

void loop(){
  int byte = mySerial.read();
  char c = (char)byte;
  if (c == ','){
    String current_string = tempdata;
    tempdata = "";
    route += current_string;
    route += "->";

  } else if (c == '\n'){
    String current_string = tempdata;
    tempdata = "";
    route += current_string;
    default_routes.push_back(route);
    route = "";
  } else {
    tempdata += c;
  }

  
  
}

