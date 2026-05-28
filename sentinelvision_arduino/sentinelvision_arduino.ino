// ESP32 Test Code
// Checks Serial, LED & Chip Info

void setup() {
  Serial.begin(115200);        // Start Serial communication
  delay(1000);
  
  Serial.println("ESP32 Test Start...");
  Serial.println();

  // Chip Info Print
  Serial.printf("Chip Cores: %d\n", ESP.getChipCores());
  Serial.printf("Chip Revision: %d\n", ESP.getChipRevision());
  Serial.printf("Flash Size: %d MB\n", ESP.getFlashChipSize() / (1024 * 1024));

  pinMode(2, OUTPUT);  // GPIO 2 par LED hoti hai (built-in LED)
}

void loop() {
  digitalWrite(2, HIGH); // LED ON
  Serial.println("LED ON");
  delay(1000);

  digitalWrite(2, LOW);  // LED OFF
  Serial.println("LED OFF");
  delay(1000);
}
