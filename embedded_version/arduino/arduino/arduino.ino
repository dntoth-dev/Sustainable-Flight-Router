#include <SoftwareSerial.h>
#include <Wire.h> 
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 20, 4); 
SoftwareSerial picoSerial(10, 11);

const int max_route_num = 5;

int def_distances[max_route_num];
int opt_distances[max_route_num];
int def_waypointCounts[max_route_num];
int opt_waypointCounts[max_route_num];


String temp_saved;
String ddist;
String odist;

String dwpcounts;
String owpcounts;

bool initialisation = true;
bool comm_over = false;

int pages = 0;
int current_page = 0;
bool lastRight = HIGH;
bool lastMode = HIGH;
bool lastLeft = HIGH;

void setup() {
  pinMode(1, INPUT_PULLUP); // button 1 - left
  pinMode(2, INPUT_PULLUP); // button 2 - mode
  pinMode(3, INPUT_PULLUP); // button 3 - right

  lcd.init();
  lcd.backlight();
  Serial.begin(9600);
  picoSerial.begin(9600);

  lcd.setCursor(0,0); // col, row
  lcd.print("Press the middle");
  lcd.setCursor(0,1);
  lcd.print("button to start!");
}

void loop() {
  int left_state = digitalRead(1);
  int mode_state = digitalRead(2);
  int right_state = digitalRead(3);

  while (initialisation == true){
    int mode_state = digitalRead(2);
    if (mode_state == LOW && lastMode == HIGH){
      lcd.clear();
      lcd.setCursor(0,0);
      lcd.print("Waiting for data...");
      picoSerial.println("@");
      initialisation = false;
      
    }
    lastMode = mode_state;
  }
  

  while (picoSerial.available() > 0){
    int data = picoSerial.read();
    char c = char(data);

    if (c == '@') {
      ddist = picoSerial.readStringUntil('\n').trim();
    } else if (c == '{') {
      odist = picoSerial.readStringUntil('\n').trim();
    } else if (c == '}') {
      dwpcounts = picoSerial.readStringUntil('\n').trim();
    } else if (c == '-') {
      owpcounts = picoSerial.readStringUntil('\n').trim();
      comm_over = true;
    }
  }




}































