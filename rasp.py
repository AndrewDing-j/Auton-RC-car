import time, serial, cv2, numpy as np
from picamera import PiCamera
from time import sleep

# Camera init
picam2 = PiCamera()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.controls.FrameRate = 30
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()
sleep(2) # Let the camera warm up

ser = serial.Serial('/dev/ttyACM0', 112500, timeout=1) # Update with your Arduino's port
ser.reset_input_buffer() # Clear any pending data
ser.reset_output_buffer()

# Define ROIs (x1, y1, x2, y2)
roi1 = [20, 170, 240, 220] # Left side
roi2 = [400, 170, 620, 220] # Right side

def drawRoi(img, roi, color=(0, 255, 0), thickness=2, label=None):
    # Draws a rectangle on the image to indicate the ROI.
    x1, y1, x2, y2 = roi
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    if label:
        cv2.putText(img, label, (x1, max(15, y1 - 8)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
    return img

def wallAreaLab(frameRgb, roi, LabLower, LabUpper, minContour = 50):
    # Calculate percentage of pixels withing the Lab range in the ROI
    x1, y1, x2, y2 = roi
    roiImg = frameRgb[y1:y2, x1:x2]
    roiLab = cv2.cvtColor(roiImg, cv2.COLOR_RGB2Lab)
    roiLab = cv2.GaussianBlur(roiLab, (7,7), 0) # larger kernel = more smoothing
    mask = cv2.inRange(roiLab, LabLower, LabUpper)

    #noice cleanup
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    areaMax = 0
    contourMax = None
    for c in contours:
        area = cv2.contourArea(c)
        if area >= minContour and area > areaMax:
            areamax = area
            contourMax = c
    if contourMax is not None:
        contourMax += [x1, y1] #shift contour points to full-frame coordinates
    return areaMax, contourMax, mask

def pidController(error, prevError, kp=0.1, kd=0.05):
    correction = kp * error + kd * (error - prevError)
    return correction

# Define thresholds
LAB_LOWER = np.array([20,120,120], dtype=np.uint8) #adjust LAB_LOWER and LAB_UPPER based on the wall colour
LAB_UPPER = np.array([70,255,255], dtype=np.uint8)
ENTER_TURN_THRESH = 550
EXIT_TURN_THRESH = 1200
EXIT_TIME_THRESH = 5.0
EXIT_ANGLE_THRESH = 85.0

# Trigger protection
CONFRIM_FRAMES = 5  # Number of consecutive frames required to confirm a turn
side = None
confirmCount = 0
turnTime = None

# Turning variables
enterTurnDegree = None
turningDegree = None

prevError = 0

mode = "STRAIGHT" #STRAIGHT, TURNING

# --- Main loop --- #
while True:
    frame = picam2.capture_array()
    now = time.monotonic()

    leftContour, leftMask, leftArea = wallAreaLab(frame, roi1, LAB_LOWER, LAB_UPPER)
    rightContour, rightMask, rightArea = wallAreaLab(frame, roi2, LAB_LOWER, LAB_UPPER)

    # --- State Machine --- #
    if mode == "STRAIGHT":
        ser.write(f"$S{pidController(leftArea-rightArea, prevError)}\n")
        if leftArea < ENTER_TURN_THRESH or rightArea < ENTER_TURN_THRESH:
            confirmCount += 1
        else:
            confirmCount = 0
        
        if confirmCount >= CONFIRM_FRAMES:
            if leftArea < rightArea:
                side = "LEFT"
            else:
                side = "RIGHT"
            confirmCount = 0
            mode = "TURNING"
            turnTime = now
            enterTurnDegree = int(ser.readline().decode().strip()) # Read current degree from Arduino's IMU
            ser.write(f"$T{leftArea-rightArea}\n") # negative result indicates "turn left" and vice versa
    
    elif mode == "TURNING":
        delta = abs(enterTurnDegree - int(ser.readline().decode()).strip())
        turningDegree = min(delta, 360 - delta) # handling of wrapping from 0 to 360 degrees
        elapsed = now - (turnTime if turnTime else now)
        if elasped > EXIT_TIME_THRESH and turningDegree > EXIT_ANGLE_THRESH:
            if (leftArea > EXIT_TURN_THRESH and side == "LEFT")\
                or (rightArea > EXIT_TURN_THRESH and side == "RIGHT"):
                mode = "STRAIGHT"
                side = None
                turnTime = None
                enterTurnDegree = None
                turningDegree = None

    # --- Visualization --- #
    drawRoi(frame, roi1, label="Left ROI")
    drawRoi(frame,roi2, label="Right ROI")

    #draw contours if found
    if leftContour:
        cv2.drawContours(frame, [leftContour], -1, (255, 0, 0), 2)
    if rightContour:
        cv2.drawContours(frame, [rightContour], -1, (255, 0, 0), 2)
    
    #numeric values for debugging
    cv2.putText(frame, f"Left Area: {leftArea}", (roi1[0], roi1[1]-40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Right Area: {rightArea}", (roi2[0], roi2[1]-40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Confirm Count: {confirmCount}", (roi1[0], 90),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Elapsed Turning Time: {now - (turnTime if turnTime else now):.2f}s", (roi1[0], roi1[3]+30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Mode: {mode}", (roi1[0], 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Side: {side}", (roi2[0], 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    #display frame
    cv2.imshow("Frame", frame)
    cv2.imshow("LeftMask", leftMask)
    cv2.imshow("RightMask", rightMask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()
picam2.stop()