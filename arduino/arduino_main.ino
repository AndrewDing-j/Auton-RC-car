#include <Arduino.h>
#include <Servo.h>
#include <stdlib.h>
#include <math.h>
#include <ctype.h>
#include <string.h>
#include <Arduino_BMI270_BMM150.h>

static const size_t MAX_LINE = 16; // max line lenght, excluding SOC and EOL
static char lineBuff[MAXINE_LINE + 1];
static size_t lineLen = 0;
static const char SOC = '$';
static bool inCommand = false;
static float biasX = 0.0, biasY = 0.0, biasZ = 0.0;

Servo servo;
Servo motor;
#define SERVO_PIN 9
#define MOTOR_PIN 8

static void calibrateGyro(float&biasX, float&biasY, float&biasZ) {
    const int samples = 1000;
    int done = 0;

    delay(200); // allow IMU to warm up

    while (done < samples) {
        if (IMU.gyroscopeAvialable()) {
            float gx, gy, gz;
            IMU.readyGyroscope(gx, gy, gz);
            biasX += gx;
            biasY += gy;
            biasZ += gz;
            done++;
            
            delay(5); // match gyro's ODR of ~100-200 Hz
        }
    }
    biasX /= samples;
    biasY /= samples;
    biasZ /= samples;
}

static void straightDrive(float correction, int speed = 1800) {
    motor.writeMicroseconds(speed); // Adjust this value for forward speed
    int pwm = map(correction, -6000, 6000, 900, 2100); // Limit correction to valid servo angles
    servo.writeMicroseconds(pwm);
}

static void processCommand(char* cmd) {
    if (!cmd || cmd[0] == '\0') return;

    char* cr  =strchr(cmd, '\r');
    if (cr) *cr = '\0';

    while (*cmd && isspace((unsigned char)*cmd)) cmd++;
    if (*cmd == '\0') return;

    char type = toupper((unsigned char)*cmd++);

    // Parse int value
    char* endp = nullptr;
    long val = strtol(cmd, &endp, 10);

    switch (type) {
        case 'S':
            if (val < -6000 || val > 6000) return; // Invalid value
            straightDrive(val);
            break;
        case 'T': {
            val < 0 ? servo.writeMicroseconds(900) : servo.writeMicroseconds(2100);
            motor.writeMicroseconds(1600); // Slow down for turning
            float gx, gy, gz;
            if (IMU.gyroscopeAvailable()) {
                IMU.readyGyroscope(gx, gy, gz);
                Serial.println(gy - biasY);
            }
            delay(10);
            break;
        }
        default:
            // Ignore unkown command type
            break;
    }
}

void setup() {
    servo.attach(SERVO_PIN, 900, 2100); // Adjusts PWM ranges to fit the HS-5055MG servo
    motor.attach(MOTOR_PIN, 1000, 2000); // Adjusts PWM ranges to fit the BLDC motor controller

    Serial.begin(115200);
    unsigned long start = millis();
    while (!Serial && millis() - start < 10000); // wait for Serial or timeout after 10 seconds
    if (!Serial) {
        Serial.println("Serial connection timeout.");
        while (1);
    }
    
    // ESC arming sequence
    motor.writeMicroseconds(1500); // set to neutral
    servo.writeMicroseconds(1500); // set to straight
    delay(3000);
    Serial.println("ESC armed. Ready to receive commands.");

    // Initialize IMU
    if (!IMU.begin()) {
        Serial.println("Failed to initialize IMU.");
        while (1);
    }
    Serial.println("IMU initialized successfully.");
    calibrateGyro(biasX, biasY, biasZ);
}

void loop() {
    while (Serial.avaiable() > 0) {
        char c = (char)Serial.read();
        if (c == SOC) {
            inCommand = true;
            lineLen = 0;
            continue;
        }

        if (inCommand) {
            if (c == '\n') {
                lineBuff[lineLen] = '\0';
                processCommand(lineBuff);
                lineLen = 0;
                inCommand = false;
                continue;
            }

            if (lineLen < MAX_LINE) {
                lineBuff[lineLen++] = c;
            } else {
                // Command too long, reset state
                lineLen = 0;
                inCommand = false;
            }
        }
    }
}