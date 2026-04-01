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

void setup() {
    servo.attach(SERVO_PIN, 900, 2100); // Adjusts PWM ranges to fit the HS-5055MG servo
    motor.attach(MOTOR_PIN, 1000, 2000); // Adjusts PWM ranges to fit the BLDC motor controller

    Serial.begin(115200);
    while (!Serial);
    
    if (!IMU.begin()) {
        Serial.println("Failed to initialize IMU.");
        while (1);
    }
    Serial.println("IMU initialized successfully.");
    calibrateGyro(biasX, biasY, biasZ);
}