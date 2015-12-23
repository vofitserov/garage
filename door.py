

import logging
import threading

import time
import RPi.GPIO as GPIO

from config import *

# Named global logger from config
logger = logging.getLogger("garage")

class GarageDoor:
    def __init__(self):
        # Use this lock to protect last known state of the door
        # for update() function called from GIO
        self.lock = threading.Lock()
        self.last_opened = 0
        self.last_closed = 0
        logger.info("initializing GPIO in BCM mode.")
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RED_LED, GPIO.OUT)
        GPIO.setup(GREEN_LED, GPIO.OUT)
        # If connected to the ground, use pull up resistor.
        GPIO.setup(SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # If the door is closed, assume the censor is working.
        if self.is_closed():
            logger.info("door is closed on init, assume sensor is working and initialized.")
            self.initialized = True
        else:
            logger.info("door is opened on init, wait until see update from sensor.")
            self.initialized = False
            pass
        
        GPIO.add_event_detect(SENSOR, GPIO.BOTH,
                      callback=lambda channel: self.update(),
                      bouncetime=300)
        return
    
    def status(self):
        message = []
        now = time.time()
        if self.initialized:
            if self.is_closed():
                message.append("door was closed %d secs ago" % int(now - self.last_closed))
                pass
            if self.is_opened():
                message.append("door was opened %d secs ago" % int(now - self.last_opened))
                pass
            if self.last_closed > self.last_opened:
                message.append("last time door was opend for %d secs" %
                               (self.last_closed - self.last_opened))
                pass
        else:
            message.append("sensor is not initialized.")
        return "<br>\n".join(message)
    
    def update(self):
        now = time.time()
        with self.lock:
            self.initialized = True
            if self.is_opened():
                self.last_opened = now
                logger.info("door was opened, last closed %d secs ago" %
                            int(now - self.last_closed))
            else:
                self.last_closed = now
                logger.info("door was closed, last opened %d secs ago" %
                            int(now - self.last_opened))
            pass
        return

    def is_opened(self):
        if GPIO.input(SENSOR) == 1:
            return True
        return False
    
    def is_closed(self):
        if GPIO.input(SENSOR) == 0:
            return True
        return False
    
    def open(self):
        now = time.time()
        with self.lock:
            if self.is_opened():
                return "Garage door is already opened."
            if not self.initialized:
                return "Garage sensor is not initialized. Open door manualy."
            logger.info("door is opening via http, last closed %d secs ago" %
                        int(now - self.last_closed))
            GPIO.output(GREEN_LED, True)
            time.sleep(1)
            GPIO.output(GREEN_LED, False)
            pass
        return "Garage door is openning..."

    def close(self):
        now = time.time()
        with self.lock:
            if self.is_closed():
                return "Garage door is already closed."
            if not self.initialized:
                return "Garage sensor is not initialized. Close door manualy."
            logger.info("door is closing via http, last opened %d secs ago" %
                        int(now - self.last_opened))
            GPIO.output(RED_LED, True)
            time.sleep(1)
            GPIO.output(RED_LED, False)
            pass
        return "Garage door is closing..."



