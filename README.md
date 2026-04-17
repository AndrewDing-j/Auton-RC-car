# Auton-RC-car
## An autonomous car powered by Raspberry Pi 5 and Arduino Nano 33 BLE Sense which can navigate through roads of various width that are flanked by walls.

### Software:
The Raspberry Pi is responsible for processing environmental data, while the Arduino serves as the controller for most peripherals, excluding the camera, and handles IMU information.
Uses a simple command protocol which allows the Arduino and Raspberry Pi to communicate with one another and interpret several commands.

### Hardware:
The chassis is that of a WL Toys K989 1:28 Scale Rally Car. All components - except for the suspension springs, wheels, bumper, and a majority of the steering mechanism - have been removed or replaced with 3DP parts.

![image](https://stasis.hackclub-assets.com/images/1776310931978-ozcrhx.png)
![image](https://stasis.hackclub-assets.com/images/1776392578242-m3uezr.png)
![image](https://stasis.hackclub-assets.com/images/1776392611197-s55ws6.png)


**Current main features include:**
---------------------------------------------------------------------
- **Auckerman Steering** (Comes as a part of the chassis and I could not find the details that would allow me to make a CAD of it)
- - Enables sharper turns
- - Smoother steering
- - Greater control at low speeds
- - Reduced tire scrubbing
- **Wide-angle Pi 5 Camera (CSI interface, 130+ FOV)**
- - Wide FOV for wall detection
- - Inexpensive, so easily replacable
- - 4K resolution
- **Raspberry Pi 5**
- - Handles visual data from camera
- - Processes visual information with the help of a Python script utilizing OpenCV
- - Reacts to the environment and sends commands to an Arduino Nano based on the data recieved
- - Generally handles driving in two states: "STRAIGHT" and "TURN"
- **Yahboom PSU Expansion Board for Raspberry Pi 5**
- - Provides stable power to Raspberry Pi 5
- - Indirectly powers Arduino Nano through Raspberry Pi 5
- - Supplied with a 2 cell 1300mAh LiPo Gens Ace battery
- **Arduino Nano 33 BLE Sense**
- - Compact
- - Controls motors and servos
- - Returns IMU gyroscopic data
- - Runs callibration script to counteract the IMU's gyroscopic drift
- - Handles commands
