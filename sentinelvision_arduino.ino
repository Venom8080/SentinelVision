/*
 * SentinelVision Defense System - Arduino Firmware
 * Controls Pan-Tilt servos and laser pointer based on serial commands
 * 
 * Commands:
 *   AUTH <name>     - Authorized face detected, turn laser OFF
 *   UNAUTH <pan> <tilt> - Unauthorized face, move servos to angles
 *   LASER_ON        - Turn laser ON
 *   LASER_OFF       - Turn laser OFF
 * 
 * Hardware:
 *   - Pan Servo: Pin 9
 *   - Tilt Servo: Pin 10
 *   - Laser Module: Pin 11
 */

#include <Servo.h>

// Pin definitions
const int PAN_SERVO_PIN = 9;
const int TILT_SERVO_PIN = 10;
const int LASER_PIN = 11;

// Servo objects
Servo panServo;
Servo tiltServo;

// Current servo positions
int panAngle = 90;  // Center position (0-180)
int tiltAngle = 90; // Center position (0-180)

// Laser state
bool laserOn = false;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port to connect (needed for native USB)
  }
  
  // Attach servos
  panServo.attach(PAN_SERVO_PIN);
  tiltServo.attach(TILT_SERVO_PIN);
  
  // Initialize servos to center position
  panServo.write(panAngle);
  tiltServo.write(tiltAngle);
  
  // Initialize laser pin
  pinMode(LASER_PIN, OUTPUT);
  digitalWrite(LASER_PIN, LOW);
  laserOn = false;
  
  // Small delay for servos to settle
  delay(500);
  
  Serial.println("SentinelVision Arduino Ready");
}

void loop() {
  // Check for incoming serial data
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove whitespace
    
    // Parse command
    if (command.startsWith("AUTH")) {
      // Authorized face detected
      handleAuthCommand(command);
    }
    else if (command.startsWith("UNAUTH")) {
      // Unauthorized face - track with servos
      handleUnauthCommand(command);
    }
    else if (command == "LASER_ON") {
      // Turn laser ON
      digitalWrite(LASER_PIN, HIGH);
      laserOn = true;
      Serial.println("Laser: ON");
    }
    else if (command == "LASER_OFF") {
      // Turn laser OFF
      digitalWrite(LASER_PIN, LOW);
      laserOn = false;
      Serial.println("Laser: OFF");
    }
    else {
      // Unknown command
      Serial.print("Unknown command: ");
      Serial.println(command);
    }
  }
  
  // Small delay to prevent overwhelming the serial buffer
  delay(10);
}

void handleAuthCommand(String cmd) {
  // Format: "AUTH <name>"
  // Extract name (optional, for logging)
  int spaceIndex = cmd.indexOf(' ');
  String name = "";
  if (spaceIndex > 0) {
    name = cmd.substring(spaceIndex + 1);
  }
  
  // Turn laser OFF
  digitalWrite(LASER_PIN, LOW);
  laserOn = false;
  
  // Optionally: return servos to center (or keep current position)
  // Uncomment below to return to center on authorized detection
  // panAngle = 90;
  // tiltAngle = 90;
  // panServo.write(panAngle);
  // tiltServo.write(tiltAngle);
  
  Serial.print("AUTH: ");
  if (name.length() > 0) {
    Serial.print(name);
    Serial.print(" - ");
  }
  Serial.println("Laser OFF");
}

void handleUnauthCommand(String cmd) {
  // Format: "UNAUTH <pan> <tilt>"
  // Extract pan and tilt angles
  int firstSpace = cmd.indexOf(' ');
  if (firstSpace < 0) {
    Serial.println("Error: UNAUTH command missing angles");
    return;
  }
  
  int secondSpace = cmd.indexOf(' ', firstSpace + 1);
  if (secondSpace < 0) {
    Serial.println("Error: UNAUTH command missing tilt angle");
    return;
  }
  
  String panStr = cmd.substring(firstSpace + 1, secondSpace);
  String tiltStr = cmd.substring(secondSpace + 1);
  
  // Convert to integers
  int newPan = panStr.toInt();
  int newTilt = tiltStr.toInt();
  
  // Constrain angles to valid range (0-180)
  newPan = constrain(newPan, 0, 180);
  newTilt = constrain(newTilt, 0, 180);
  
  // Update servo positions
  panAngle = newPan;
  tiltAngle = newTilt;
  
  panServo.write(panAngle);
  tiltServo.write(tiltAngle);
  
  // Optional: Print for debugging
  // Serial.print("Tracking: Pan=");
  // Serial.print(panAngle);
  // Serial.print(", Tilt=");
  // Serial.println(tiltAngle);
}

