/*
 * CORRECT Arduino Code for LED Control
 * LED turns ON only when object detected
 */

const int LED_PIN = 13;  // Built-in LED on Arduino Uno
int ledState = LOW;      // Track LED state

void setup() {
  Serial.begin(9600);     // Match with Python
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);  // Start with LED OFF
  Serial.println("ARDUINO READY");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();  // Remove whitespace
    
    // Clear any previous responses
    if (command == "ON") {
      digitalWrite(LED_PIN, HIGH);
      ledState = HIGH;
      Serial.println("LED:ON");  // Simple response without spaces
      Serial.flush();  // Ensure data is sent
    }
    else if (command == "OFF") {
      digitalWrite(LED_PIN, LOW);
      ledState = LOW;
      Serial.println("LED:OFF");
      Serial.flush();
    }
    else if (command == "STATUS") {
      if (ledState == HIGH) {
        Serial.println("STATUS:ON");
      } else {
        Serial.println("STATUS:OFF");
      }
      Serial.flush();
    }
    else if (command == "BLINK") {
      // Blink 3 times for visual feedback
      for(int i = 0; i < 3; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(200);
        digitalWrite(LED_PIN, LOW);
        delay(200);
      }
      Serial.println("BLINK:DONE");
      Serial.flush();
    }
  }
  
  // Small delay to prevent overwhelming the serial buffer
  delay(10);
}