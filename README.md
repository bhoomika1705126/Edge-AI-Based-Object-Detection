// Arduino LED Control Code
const int ledPin = 13;  // Built-in LED
String inputString = "";

void setup() {
  Serial.begin(9600);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
  Serial.println("Arduino Ready");
}

void loop() {
  if (Serial.available() > 0) {
    inputString = Serial.readStringUntil('\n');
    inputString.trim();
    
    if (inputString == "ON") {
      digitalWrite(ledPin, HIGH);
      Serial.println("LED:ON");
    }
    else if (inputString == "OFF") {
      digitalWrite(ledPin, LOW);
      Serial.println("LED:OFF");
    }
    else if (inputString == "BLINK") {
      for(int i = 0; i < 5; i++) {
        digitalWrite(ledPin, HIGH);
        delay(200);
        digitalWrite(ledPin, LOW);
        delay(200);
      }
      Serial.println("LED:BLINKED");
    }
    else if (inputString == "STATUS") {
      if (digitalRead(ledPin) == HIGH) {
        Serial.println("STATUS:ON");
      } else {
        Serial.println("STATUS:OFF");
      }
    }
  }
}
