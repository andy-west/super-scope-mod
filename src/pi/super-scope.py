import cv2
import numpy
import os
import RPi.GPIO as GPIO
import time
import serial

from imutils import perspective

TRACKING_WIDTH = 51
BLACK_BAR_WIDTH = 8
WIDE_TRACKING_WIDTH = TRACKING_WIDTH + BLACK_BAR_WIDTH * 2
TRACKING_HEIGHT = 231

TURBO_PIN = 5
POWER_ON_PIN = 6
PAUSE_BUTTON_PIN = 13
TRIGGER_BUTTON_PIN = 19
CURSOR_BUTTON_PIN = 26

BT_MESSAGE_TRIGGER_PRESSED = 231
BT_MESSAGE_TRIGGER_RELEASED = 232
BT_MESSAGE_CURSOR_PRESSED = 233
BT_MESSAGE_CURSOR_RELEASED = 234
BT_MESSAGE_TURBO_ENABLED = 235
BT_MESSAGE_TURBO_DISABLED = 236
BT_MESSAGE_PAUSE_PRESSED = 237
BT_MESSAGE_PAUSE_RELEASED = 238
BT_MESSAGE_TV_NOT_VISIBLE = 239
BT_MESSAGE_AIM_X = 240
BT_MESSAGE_AIM_Y = 241

isTvVisible = False

GPIO.setmode(GPIO.BCM)

GPIO.setup(TURBO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(POWER_ON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(PAUSE_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(TRIGGER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(CURSOR_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

serialPort = serial.Serial(port = "/dev/rfcomm0")

def handleButtons(channel):
    isRising = GPIO.input(channel)

    if channel == TURBO_PIN:
        serialPort.write(bytearray([BT_MESSAGE_TURBO_ENABLED]) if isRising else bytearray([BT_MESSAGE_TURBO_DISABLED]))
    elif channel == POWER_ON_PIN:
        if not isRising:
            os.system("shutdown now -h")
    elif channel == PAUSE_BUTTON_PIN:
        serialPort.write(bytearray([BT_MESSAGE_PAUSE_PRESSED]) if isRising else bytearray([BT_MESSAGE_PAUSE_RELEASED]))
    elif channel == TRIGGER_BUTTON_PIN:
        serialPort.write(bytearray([BT_MESSAGE_TRIGGER_PRESSED]) if isRising else bytearray([BT_MESSAGE_TRIGGER_RELEASED]))
    elif channel == CURSOR_BUTTON_PIN:
        serialPort.write(bytearray([BT_MESSAGE_CURSOR_PRESSED]) if isRising else bytearray([BT_MESSAGE_CURSOR_RELEASED]))

handleButtons(TURBO_PIN)

GPIO.add_event_detect(TURBO_PIN, GPIO.BOTH, callback = handleButtons, bouncetime = 10)
GPIO.add_event_detect(POWER_ON_PIN, GPIO.BOTH, callback = handleButtons, bouncetime = 10)
GPIO.add_event_detect(PAUSE_BUTTON_PIN, GPIO.BOTH, callback = handleButtons, bouncetime = 10)
GPIO.add_event_detect(TRIGGER_BUTTON_PIN, GPIO.BOTH, callback = handleButtons, bouncetime = 10)
GPIO.add_event_detect(CURSOR_BUTTON_PIN, GPIO.BOTH, callback = handleButtons, bouncetime = 10)

camera = cv2.VideoCapture(0)

if camera.isOpened():
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

windowName = "Super Scope"
cv2.namedWindow(windowName)

while True:
    wasFrameGrabSuccessful, frame = camera.read()

    if wasFrameGrabSuccessful:
        grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(grayFrame, 127, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        finalFrame = cv2.cvtColor(grayFrame, cv2.COLOR_GRAY2BGR)

        trackingPointCount = 0
        trackingPoints = numpy.zeros(shape = (4, 2), dtype = numpy.float32)

        for contour in contours:
            moments = cv2.moments(contour)

            if moments["m00"] > 10:
                if trackingPointCount < 5:
                    centerX = int(moments["m10"] / moments["m00"])
                    centerY = int(moments["m01"] / moments["m00"])
                    trackingPoints[trackingPointCount] = [centerX, centerY]
                    cv2.circle(finalFrame, (centerX, centerY), 5, (0, 255, 0), cv2.FILLED)

                trackingPointCount += 1

        trackingPoints = perspective.order_points(trackingPoints)

        # Draw red dot at center.
        cv2.circle(finalFrame, (320, 240), 5, (0, 0, 255), cv2.FILLED)

        # Outline transformed area in blue.
        cv2.rectangle(finalFrame, (0, 0), (TRACKING_WIDTH, TRACKING_HEIGHT), (255, 0, 0), 3)

        if trackingPointCount == 4:
            destPoints = numpy.array([[0, 0], [WIDE_TRACKING_WIDTH - 1, 0], [WIDE_TRACKING_WIDTH - 1, TRACKING_HEIGHT - 1], [0, TRACKING_HEIGHT - 1]], dtype = numpy.float32)
            transform = cv2.getPerspectiveTransform(trackingPoints[:, numpy.newaxis, :], destPoints[:, numpy.newaxis, :])
            transformed = cv2.perspectiveTransform(numpy.array([[320, 240]], dtype = numpy.float32)[:, numpy.newaxis, :], transform)

            transformedX = int(transformed[0][0][0] - BLACK_BAR_WIDTH)
            transformedY = int(transformed[0][0][1])

            # Draw transformed tracking point in yellow.
            cv2.circle(finalFrame, (transformedX, transformedY), 5, (0, 255, 255), cv2.FILLED)

            if (0 <= transformedX < TRACKING_WIDTH) and (0 <= transformedY < TRACKING_HEIGHT):
                isTvVisible = True;
                serialPort.write(bytearray([BT_MESSAGE_AIM_X, transformedX, BT_MESSAGE_AIM_Y, transformedY]))
            elif isTvVisible:
                isTvVisible = False;
                serialPort.write(bytearray([BT_MESSAGE_TV_NOT_VISIBLE]))
        elif isTvVisible:
            isTvVisible = False;
            serialPort.write(bytearray([BT_MESSAGE_TV_NOT_VISIBLE]))

        cv2.imshow(windowName, finalFrame)

    if cv2.waitKey(1) % 0xFF == 27:  # Escape key
        break

camera.release()
cv2.destroyAllWindows()
GPIO.cleanup()
