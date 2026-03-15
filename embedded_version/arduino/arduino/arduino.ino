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

/*
int default_routes_distances[max_route_num];
int optimised_routes_distances[max_route_num];
int default_waypoint_counts[max_route_num];
int optimised_waypoint_counts[max_route_num];
*/

String dd[max_route_num];
Vector<String> default_routes_distances(dd);

String od[max_route_num];
Vector<String> optimised_routes_distances(od);

String dw[max_route_num];
Vector<String> default_waypoint_counts(dw);

String ow[max_route_num];
Vector<String> optimised_waypoint_counts(ow);

/*
String storage[max_route_num];
Vector<String> default_routes(storage);
*/

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
bool is_route_view = true;

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

void loop(){

  int left_state = digitalRead(1);
  int mode_state = digitalRead(2);
  int right_state = digitalRead(3);

  /*
  while (picoSerial.available()){
    int byte = picoSerial.read();
    char c = (char)byte;
    if (c == ','){
      String current_string = tempdata;
      tempdata = "";
      route += current_string;
      route += "->";

    } else if (c == '|'){
      String current_string = tempdata;
      tempdata = "";
      route += current_string;
      default_routes.push_back(route);
      route = "";
    } else {
      tempdata += c;
    }
  }
  */
  // Read data when available
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

  if (right_state == LOW && lastRight == HIGH){
    lcd.clear();
    lcd.setCursor(0,0);
    lcd.print(default_routes_distances[1]);
    lcd.setCursor(0,1);
    lcd.print(optimised_routes_distances[1]);
  }
  lastRight = right_state;
}
/*
  int left_state = digitalRead(1); 
  if (left_state == LOW && lastLeft == HIGH) {
    Serial.println("--- Current Data ---");
    Serial.println(def_distances);
    Serial.println(opt_distances);
  }
  lastLeft = left_state;
}
*/

/*
  int left_state = digitalRead(1);
  int mode_state = digitalRead(2);
  int right_state = digitalRead(3);
  
  if (right_state == LOW && lastRight == HIGH){
    is_route_view = true;
    lcd.clear();
    if (current_page < pages){
      current_page++;
    } else {
      current_page = 1;
    }
    String line1 = "Route " + String(current_page) + ":";
    String route = default_routes[current_page-1];
    lcd.setCursor(0,0);
    lcd.print(line1);
    scrollSecondRow(route);
  }
  lastRight = right_state;

  if (left_state == LOW && lastLeft == HIGH){
    is_route_view = true;
    lcd.clear();
    if (current_page > 1){
      current_page--;
    } else {
      current_page = pages;
    }
    lcd.setCursor(0,0);
    lcd.print("Route " + String(current_page) + ":");
    lcd.setCursor(0,1);
    lcd.print(default_routes[current_page-1]);
  }
  lastLeft = left_state;
  /*
  if (mode_state == LOW && lastMode == HIGH){
    lcd.clear();
    if (is_route_view == true){
      lcd.clear();
      is_route_view == false;
      lcd.setCursor(0,0);
      lcd.print("Route " + String(current_page) + " stats:");
      lcd.setCursor(0,1);
      lcd.print(default_routes_stats[current_page-1]);
    }
    if (is_route_view == false){
      lcd.clear();
      is_route_view = true;
      lcd.setCursor(0,0);
      lcd.print("Route " + String(current_page) + ":");
      lcd.setCursor(0,1);
      lcd.print(default_routes[current_page-1]);
    }
  }
  lastMode = mode_state;
  */
/*
  if (is_route_view && current_page > 0) {
    scrollSecondRow(default_routes[current_page - 1]);
  }
  
}

void scrollSecondRow(String text) {
  if (text.length() <= 20) {
    lcd.setCursor(0, 1);
    lcd.print(text);
    return;
  }

  if (millis() - lastScrollTime >= scrollDelay) {
    lastScrollTime = millis();

    lcd.setCursor(0, 1);

    for (int i = 0; i < 20; i++) {
      int index = (scrollIndex + i) % text.length();
      lcd.print(text[index]);
    }

    scrollIndex++;
    if (scrollIndex >= text.length()) {
      scrollIndex = 0;
    }
  }
  
}
*/