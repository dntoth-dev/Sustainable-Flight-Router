#include <SoftwareSerial.h>
#include <Wire.h> 
#include <LiquidCrystal_I2C.h>
#include <Vector.h>

LiquidCrystal_I2C lcd(0x27, 20, 4); 
SoftwareSerial picoSerial(10, 11);

unsigned long lastScrollTime = 0;
const int scrollDelay = 300;
int scrollIndex = 0;

const int max_route_num = 5;
const int max_wp_num = 10;

String dd[max_route_num];
Vector<String> default_routes_distances(dd);

String od[max_route_num];
Vector<String> optimised_routes_distances(od);

String dw[max_route_num];
Vector<String> default_waypoint_counts(dw);

String ow[max_route_num];
Vector<String> optimised_waypoint_counts(ow);

String temp_saved;
String def_distances;
String opt_distances;

String def_wpcounts;
String opt_wpcounts;

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

  lcd.setCursor(0,0);
  lcd.print("Waiting for data...");
}

void loop() {
  int left_state = digitalRead(1);
  int mode_state = digitalRead(2);
  int right_state = digitalRead(3);

  while (picoSerial.available() > 0) {
    char c = picoSerial.read();
    
    if (c == '/') {
      def_distances = picoSerial.readStringUntil('@');
    } else if (c == '-') {
      opt_distances = picoSerial.readStringUntil('~');
    } else if (c == '_') {
      def_wpcounts = picoSerial.readStringUntil('`');
    } else if (c == '?') {
      opt_wpcounts = picoSerial.readStringUntil('=');
    }
  }

  for (char c: def_distances) {
    if (c == ','){
      default_routes_distances.push_back(temp_saved);
      temp_saved = "";
    } else {
      temp_saved += c;
    }
  }

  for (char c: opt_distances) {
    if (c == ','){
      optimised_routes_distances.push_back(temp_saved);
      temp_saved = "";
    } else {
      temp_saved += c;
    }
  }

  for (char c: def_wpcounts) {
    if (c == ','){
      default_waypoint_counts.push_back(temp_saved);
      temp_saved = "";
    } else {
      temp_saved += c;
    }
  }

  for (char c: opt_wpcounts) {
    if (c == ','){
      optimised_waypoint_counts.push_back(temp_saved);
      temp_saved = "";
    } else {
      temp_saved += c;
    }
  }

  for (String item: default_routes_distances){
    if (item != ""){
      pages++;
    }
  }

  if (right_state == LOW && lastRight == HIGH){
    lcd.clear();
    if (current_page < pages){
      current_page++;
    } else {
      current_page = 1;
    }

    lcd.setCursor(0,0);
    lcd.print("Route " + String(current_page) + " default:");
    lcd.setCursor(0,1);
    int wpc = default_waypoint_counts[current_page-1].toInt();
    lcd.print("Pts:" + default_waypoint_counts[wpc] + " Len:" + default_waypoint_counts[current_page-1]);
  }
  lastRight = right_state;


}































