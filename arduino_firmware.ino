/*
 * SentinelVision Defense System - Arduino Firmware
 * Controls Pan-Tilt servos and laser pointer based on face tracking commands
 * 
 * Commands:
 * - AUTH <name>     : Authorized face detected, turn off laser
 * - UNAUTH <pan> <tilt> : Unauthorized face, move servos to pan/tilt angles
 * - LASER_ON        : Turn laser on
 * - LASER_OFF       : Turn laser off
 */

#include <Servo.h>

// Pin definitions
const int PAN_SERVO_PIN = 9;      // Pan servo (horizontal)
const int TILT_SERVO_PIN = 10;     // Tilt servo (vertical)
const int LASER_PIN = 11;          // Laser module control pin

// Servo objects
Servo panServo;
Servo tiltServo;

// Current servo positions
int panAngle = 90;   // Center position (0-180)
int tiltAngle = 90;  // Center position (0-180)

// Laser state
bool laserOn = false;

// Serial buffer
String inputString = "";
bool stringComplete = false;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.setTimeout(100);
  
  // Initialize servos
  panServo.attach(PAN_SERVO_PIN);
  tiltServo.attach(TILT_SERVO_PIN);
  
  // Set servos to center position
  panServo.write(panAngle);
  tiltServo.write(tiltAngle);
  
  // Initialize laser pin
  pinMode(LASER_PIN, OUTPUT);
  digitalWrite(LASER_PIN, LOW);
  laserOn = false;
  
  // Reserve space for serial input
  inputString.reserve(100);
  
  // Wait for serial connection (optional)
  delay(1000);
  
  // Send ready message
  Serial.println("SentinelVision Arduino Ready");
}

void loop() {
  // Read serial commands
  if (Serial.available() > 0) {
    inputString = Serial.readStringUntil('\n');
    inputString.trim();
    
    if (inputString.length() > 0) {
      processCommand(inputString);
    }
  }
  
  // Small delay to prevent overwhelming the serial buffer
  delay(10);
}

void processCommand(String cmd) {
  // Parse command
  cmd.toUpperCase();
  
  if (cmd.startsWith("AUTH")) {
    // Authorized face detected
    // Format: AUTH <name>
    handleAuth(cmd);
    
  } else if (cmd.startsWith("UNAUTH")) {
    // Unauthorized face - track it
    // Format: UNAUTH <pan_angle> <tilt_angle>
    handleUnauth(cmd);
    
  } else if (cmd == "LASER_ON") {
    // Turn laser on
    digitalWrite(LASER_PIN, HIGH);
    laserOn = true;
    Serial.println("LASER: ON");
    
  } else if (cmd == "LASER_OFF") {
    // Turn laser off
    digitalWrite(LASER_PIN, LOW);
    laserOn = false;
    Serial.println("LASER: OFF");
    
  } else {
    // Unknown command
    Serial.print("Unknown command: ");
    Serial.println(cmd);
  }
}

void handleAuth(String cmd) {
  // Authorized face - turn off laser, keep servos in center
  digitalWrite(LASER_PIN, LOW);
  laserOn = false;
  
  // Optionally move servos to center (smooth movement)
  smoothMoveServos(90, 90);
  
  // Extract name if provided
  int nameStart = cmd.indexOf(' ');
  if (nameStart > 0) {
    String name = cmd.substring(nameStart + 1);
    Serial.print("AUTH: Welcome ");
    Serial.println(name);
  } else {
    Serial.println("AUTH: Authorized");
  }
}

void handleUnauth(String cmd) {
  // Unauthorized face - track with servos
  // Format: UNAUTH <pan> <tilt>
  
  int firstSpace = cmd.indexOf(' ');
  int secondSpace = cmd.indexOf(' ', firstSpace + 1);
  
  if (firstSpace > 0 && secondSpace > 0) {
    int newPan = cmd.substring(firstSpace + 1, secondSpace).toInt();
    int newTilt = cmd.substring(secondSpace + 1).toInt();
    
    // Clamp values to valid servo range
    newPan = constrain(newPan, 0, 180);
    newTilt = constrain(newTilt, 0, 180);
    
    // Move servos smoothly
    smoothMoveServos(newPan, newTilt);
    
    Serial.print("UNAUTH: Tracking Pan=");
    Serial.print(newPan);
    Serial.print(" Tilt=");
    Serial.println(newTilt);
  } else {
    Serial.println("UNAUTH: Invalid format");
  }
}

void smoothMoveServos(int targetPan, int targetTilt) {
  // Smooth servo movement to prevent jitter
  int panStep = (targetPan > panAngle) ? 1 : -1;
  int tiltStep = (targetTilt > tiltAngle) ? 1 : -1;
  
  // Move servos gradually
  while (panAngle != targetPan || tiltAngle != targetTilt) {
    if (panAngle != targetPan) {
      panAngle += panStep;
      if ((panStep > 0 && panAngle > targetPan) || 
          (panStep < 0 && panAngle < targetPan)) {
        panAngle = targetPan;
      }
      panServo.write(panAngle);
    }
    
    if (tiltAngle != targetTilt) {
      tiltAngle += tiltStep;
      if ((tiltStep > 0 && tiltAngle > targetTilt) || 
          (tiltStep < 0 && tiltAngle < targetTilt)) {
        tiltAngle = targetTilt;
      }
      tiltServo.write(tiltAngle);
    }
    
    delay(15); // Small delay for smooth movement
  }
}

